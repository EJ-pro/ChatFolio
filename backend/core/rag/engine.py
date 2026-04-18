from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
# Chroma 대신 순수 파이썬 인메모리 스토어 사용
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage

class ChatFolioEngine:
    def __init__(self, files_data, graph, provider="groq", model_name=None):
        self.files_data = files_data
        self.graph = graph
        
        # LLM 초기화
        if provider == "openai":
            self.llm = ChatOpenAI(model=model_name or "gpt-4o-mini", temperature=0)
        else: # Default is groq
            self.llm = ChatGroq(model=model_name or "llama-3.3-70b-versatile", temperature=0)
            
        self.embeddings = OpenAIEmbeddings()
        
        # 1. 벡터 스토어 구축
        self.vector_db = self._prepare_vector_db()

    def _prepare_vector_db(self):
        # 코드를 의미 있는 단위로 쪼개기
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100,
            separators=["\nfun ", "\nclass ", "\ninterface ", "\n\n", "\n"]
        )
        
        docs = []
        for path, content in self.files_data.items():
            chunks = text_splitter.split_text(content)
            for chunk in chunks:
                docs.append({"page_content": chunk, "metadata": {"path": path}})
        
        texts = [d["page_content"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        
        # Chroma 대신 InMemoryVectorStore 사용! (설치/충돌 이슈 0%)
        return InMemoryVectorStore.from_texts(texts, self.embeddings, metadatas=metadatas)

    def ask(self, query: str):
        # 2. 관련 파일 검색
        related_docs = self.vector_db.similarity_search(query, k=3)
        
        sources = []
        visited_nodes = []
        context_paths = set()

        for doc in related_docs:
            path = doc.metadata['path']
            context_paths.add(path)
            
            if not any(s['path'] == path for s in sources):
                sources.append({"path": path, "reason": "Vector Similarity"})
            
            # 3. 그래프 탐색 (이웃 노드 추적)
            if path in self.graph:
                neighbors = list(self.graph.neighbors(path))
                for n in neighbors[:2]: 
                    context_paths.add(n)
                    if not any(s['path'] == n for s in sources):
                        file_name = path.split('/')[-1]
                        sources.append({"path": n, "reason": f"Dependency (from {file_name})"})
                    visited_nodes.append({"from": path, "to": n})

        # 4. 컨텍스트 구성
        context_text = ""
        for path in context_paths:
            if path in self.files_data:
                context_text += f"\n--- File: {path} ---\n{self.files_data[path][:2500]}\n"

        # 5. LLM 프롬프트
        system_prompt = SystemMessage(content="""
        당신은 숙련된 안드로이드(Kotlin) 개발자이자 코드 분석가입니다. 
        주어진 코드베이스 컨텍스트를 바탕으로 사용자의 질문에 답변하세요.
        
        [답변 규칙]
        1. 핵심 로직이나 함수, 클래스를 설명할 때는 반드시 [파일명] 또는 [파일명:라인번호] 형식으로 출처를 명시하세요.
        2. 파일 간의 연결 관계를 설명해주면 좋습니다.
        3. 모르는 내용은 추측하지 말고 모른다고 답하세요.
        """)
        
        user_prompt = HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {query}")
        
        # 6. 답변 생성
        response = self.llm.invoke([system_prompt, user_prompt])
        
        return {
            "answer": response.content,
            "sources": sources,
            "graph_trace": visited_nodes
        }

    def generate_mermaid(self) -> str:
        if not self.llm:
            return "graph TD\n    A[LLM Not Configured]"
            
        nodes = list(self.graph.nodes())
        nodes_str = "\n".join(nodes)
        
        system_prompt = SystemMessage(content="""
        당신은 소프트웨어 아키텍트입니다. 다음은 안드로이드/소프트웨어 프로젝트의 파일 경로 목록입니다.
        이 파일들을 도메인이나 역할(예: Adapter, Fragment, Model, Network 등)에 따라 그룹화하세요.
        
        [출력 형식 - 반드시 JSON만 출력하세요]
        ```json
        {
          "subgraphs": [
            {
              "name": "Adapter",
              "nodes": ["app/src/main/.../Adapter.kt", "app/.../AnotherAdapter.kt"]
            },
            {
              "name": "Fragment",
              "nodes": ["app/src/main/.../Fragment.kt"]
            }
          ]
        }
        ```
        """)
        
        user_prompt = HumanMessage(content=f"Files:\n{nodes_str}")
        
        try:
            response = self.llm.invoke([system_prompt, user_prompt])
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            grouping = json.loads(content)
            
            # 1. 안전한 노드 ID 매핑 생성
            node_id_map = {}
            for i, node in enumerate(nodes):
                node_id_map[node] = f"Node_{i}"
                
            # 2. Mermaid 코드 조합
            mermaid_lines = ["graph TD"]
            
            # 서브그래프 작성
            used_nodes = set()
            for sg in grouping.get("subgraphs", []):
                name = sg.get("name", "Unknown").replace(" ", "_").replace('"', '')
                mermaid_lines.append(f"    subgraph {name}")
                for node in sg.get("nodes", []):
                    if node in node_id_map:
                        node_id = node_id_map[node]
                        display_name = node.split('/')[-1]
                        mermaid_lines.append(f'        {node_id}["{display_name}"]')
                        used_nodes.add(node)
                mermaid_lines.append("    end")
                
            # 그룹화되지 않은 노드들
            for node in nodes:
                if node not in used_nodes:
                    node_id = node_id_map[node]
                    display_name = node.split('/')[-1]
                    mermaid_lines.append(f'    {node_id}["{display_name}"]')
                    
            mermaid_lines.append("")
            
            # 엣지(의존성) 작성
            for u, v in self.graph.edges():
                if u in node_id_map and v in node_id_map:
                    mermaid_lines.append(f"    {node_id_map[u]} --> {node_id_map[v]}")
                    
            return "\n".join(mermaid_lines)
            
        except Exception as e:
            # 실패 시 단순 폴백 반환
            print(f"Mermaid generation failed: {e}")
            fallback_lines = ["graph TD"]
            node_id_map = {node: f"N_{i}" for i, node in enumerate(nodes)}
            for node, nid in node_id_map.items():
                fallback_lines.append(f'    {nid}["{node.split("/")[-1]}"]')
            for u, v in self.graph.edges():
                if u in node_id_map and v in node_id_map:
                    fallback_lines.append(f"    {node_id_map[u]} --> {node_id_map[v]}")
            return "\n".join(fallback_lines)

    def generate_readme(self, template: str = "default") -> str:
        if not self.llm:
            return "# README\n\nLLM이 구성되지 않았습니다."
            
        nodes = list(self.graph.nodes())
        file_count = len(nodes)
        
        # 1. 의존성 매니페스트 파일 찾기 (기술 스택 파악용)
        manifest_content = ""
        for path, content in self.files_data.items():
            if any(m in path.lower() for m in ["build.gradle", "package.json", "pom.xml", "requirements.txt"]):
                manifest_content += f"\n--- {path} ---\n{content[:1500]}\n"
        
        # 2. 가장 많이 참조된 Top 5 핵심 파일 코드 스니펫 추출
        in_degrees = dict(self.graph.in_degree())
        top_files = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        top_files_str = "\n".join([f"- {f} (참조됨: {count}회)" for f, count in top_files])
        
        core_files_code = ""
        for f, _ in top_files:
            if f in self.files_data:
                # 각 핵심 파일의 첫 800자 제공 (클래스 정의, 주요 메서드 파악)
                core_files_code += f"\n--- {f} ---\n{self.files_data[f][:800]}...\n"
        
        # 3. 디렉토리 구조 생성 (트리 형태)
        import os
        dirs = set()
        for node in nodes:
            dirs.add(os.path.dirname(node))
        dir_str = "\n".join([f"- {d}" for d in sorted(list(dirs))[:30]])
        
        context = f"""
        [프로젝트 정보 요약]
        - 총 파일 수: {file_count}개
        
        [주요 디렉토리 구조]
        {dir_str}

        [기술 스택 정보 (매니페스트 파일)]
        {manifest_content}
        
        [가장 많이 참조된 핵심 파일 Top 5 및 코드 스니펫]
        {top_files_str}
        {core_files_code}
        """
        
        template_prompts = {
            "default": """
            [스타일: Standard Professional]
            가장 표준적이고 전문적인 실리콘밸리 오픈소스 스타일.
            - 헤더, 주요 기능, 기술 스택, 아키텍처, 폴더 구조를 균형있게 포함.
            - 적절한 이모지와 뱃지 사용.
            - 분량: 1500자 이상 상세하게.
            """,
            "minimal": """
            [스타일: Minimalist & Clean]
            핵심만 간결하게 전달하는 깔끔한 미니멀 스타일.
            - 장황한 설명을 생략하고 요점만 빠르게 전달.
            - 뱃지, 프로젝트 이름, 한 줄 소개, 빠른 시작(Quick Start), 핵심 기능 3줄 요약.
            - 이모지 사용을 최소화하고 텍스트 가독성에 집중.
            - 분량: 500자 내외 핵심 위주.
            """,
            "academic": """
            [스타일: Academic & Research]
            연구나 학술 프로젝트에 적합한 깊이 있는 아키텍처 중심 문서.
            - 시스템 설계 배경, 디자인 패턴, 알고리즘, 컴포넌트 간의 데이터 흐름에 집중.
            - 왜 이 아키텍처를 선택했는지 심도 깊은 분석 제공.
            - 논문 초록(Abstract)처럼 시작하여, 방법론(Methodology) 및 구현 세부사항(Implementation Details) 섹션 포함.
            - 분량: 2000자 이상 매우 상세하게.
            """,
            "startup": """
            [스타일: Startup Pitch & Product]
            비즈니스 가치와 제품 관점에서 어필하는 스타트업 피칭 스타일.
            - "이 프로덕트가 왜 가치 있는가?(Value Proposition)"에 집중.
            - 유저 관점의 주요 기능(Features)과 비즈니스 로직 강조.
            - 엄청나게 많은 이모지와 화려한 마크다운 요소 사용. "🚀", "✨", "🔥" 등을 적극 활용.
            - 세일즈 피치처럼 매력적으로 작성.
            """,
            "detailed": """
            [스타일: Extremely Detailed Documentation]
            거의 모든 컴포넌트와 파일을 뜯어 설명하는 방대한 개발자 가이드 스타일.
            - 프로젝트의 모든 주요 클래스, 함수, 폴더 역할을 최대한 길고 상세하게 나열.
            - 환경 설정, 트러블슈팅, 향후 개선점(Roadmap) 섹션 포함.
            - 분량: 3000자 이상 가능한 한 길게.
            """
        }
        
        selected_style = template_prompts.get(template, template_prompts["default"])
        
        system_prompt = SystemMessage(content=f"""
        당신은 탑티어 시니어 테크니컬 라이터입니다.
        제공된 프로젝트 코드 스니펫과 구조를 바탕으로 GitHub README.md를 마크다운으로 작성하세요.

        {selected_style}

        코드를 읽고 '이 앱이 정확히 무슨 기능을 하는지' 깊이 있게 추론하여 상세히 적어야 합니다.
        응답은 오직 README.md 마크다운 코드만 출력하세요. 다른 말은 절대 금지합니다.
        """)
        
        user_prompt = HumanMessage(content=context)
        
        response = self.llm.invoke([system_prompt, user_prompt])
        content = response.content.strip()
        
        if "```markdown" in content:
            content = content.split("```markdown")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return content