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

    def generate_readme(self) -> str:
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
        
        system_prompt = SystemMessage(content="""
        당신은 실리콘밸리 탑티어 오픈소스 메인테이너이자 시니어 테크니컬 라이터입니다.
        제공된 프로젝트의 의존성 구조, 매니페스트 파일(build.gradle 등), 그리고 핵심 파일의 실제 코드 스니펫을 분석하여 
        최고급 퀄리티의 GitHub README.md를 마크다운으로 작성하세요.

        단순한 나열이 절대 아닙니다. 코드를 읽고 '이 앱이 정확히 무슨 기능을 하는지' 깊이 있게 추론하여 상세히 적어야 합니다.

        [반드시 포함할 내용 및 양식]
        1. **프로젝트 헤더**: 프로젝트 이름 (멋지게 추론), 뱃지들 (기술 스택 기반 마크다운 뱃지), 한 줄 소개.
        2. **✨ 주요 기능 (Key Features)**: 핵심 코드 스니펫을 읽고 이 앱이 어떤 비즈니스 로직(로그인, 메모, 매칭 등)을 수행하는지 구체적으로 3~5가지 작성.
        3. **🛠 기술 스택 (Tech Stack)**: 제공된 매니페스트(build.gradle 등)에 명시된 라이브러리 버전을 포함하여 상세히 분류 (Frontend, Backend, Database 등).
        4. **🏗 아키텍처 및 핵심 컴포넌트 (Architecture)**: Top 5 파일들이 어떤 역할을 하며 서로 어떻게 데이터를 주고받는지(MVVM, Clean Architecture 등) 심층 분석.
        5. **📂 폴더 구조 (Project Structure)**: 주요 디렉토리를 ASCII Tree 구조로 멋지게 포매팅.
        
        [작성 가이드라인]
        - 이모지(Emoji)를 적절히 활용하여 시각적으로 아름답게 꾸미세요.
        - 분량은 아주 상세하고 깁니다 (최소 1500자 이상). 절대 짧게 대충 쓰지 마세요.
        - 개발자가 이 README만 보고도 프로젝트 전체 흐름을 완벽히 이해할 수 있도록 '전문적이고 세련된 어투'로 작성하세요.
        - 응답은 오직 README.md 마크다운 코드만 출력하세요.
        """)
        
        user_prompt = HumanMessage(content=context)
        
        response = self.llm.invoke([system_prompt, user_prompt])
        content = response.content.strip()
        
        if "```markdown" in content:
            content = content.split("```markdown")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return content