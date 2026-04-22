from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
# Chroma 대신 순수 파이썬 인메모리 스토어 사용
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage

class ChatFolioEngine:
    def __init__(self, files_data, graph, tech_stack=None, provider="groq", model_name=None):
        self.files_data = files_data
        self.graph = graph
        self.tech_stack = tech_stack # {main_language, frameworks, used_parsers, language_distribution}
        
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
            # 다양한 언어의 정의부(fun, def, fn, class, func 등)를 고려한 구분자
            separators=["\nclass ", "\ndef ", "\nfn ", "\nfun ", "\nfunc ", "\ninterface ", "\nmodule ", "\n\n", "\n"]
        )
        
        docs = []
        # generator나 dict 모두 순회 가능하도록 처리
        items = self.files_data.items() if isinstance(self.files_data, dict) else self.files_data
        
        for path, content in items:
            chunks = text_splitter.split_text(content)
            for chunk in chunks:
                docs.append({"page_content": chunk, "metadata": {"path": path}})
        
        if not docs:
            # 문서가 없는 경우 빈 리스트 대신 더미 문서라도 추가하여 초기화 에러 방지
            return InMemoryVectorStore.from_texts([" "], self.embeddings, metadatas=[{"path": "none"}])

        texts = [d["page_content"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        
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
        tech_context = ""
        if self.tech_stack:
            tech_context = f"\n[Project Tech Stack]\n- Main Language: {self.tech_stack.get('main_language')}\n- Frameworks: {', '.join(self.tech_stack.get('frameworks', []))}\n- Used Parsers: {', '.join(self.tech_stack.get('used_parsers', []))}\n"

        system_prompt = SystemMessage(content=f"""
        당신은 숙련된 풀스택 소프트웨어 엔지니어이자 코드 분석가입니다. 
        다양한 프로그래밍 언어와 프레임워크에 정통하며, 주어진 코드베이스 컨텍스트를 바탕으로 사용자의 질문에 전문적이고 정확하게 답변합니다.
        {tech_context}
        
        [답변 규칙]
        1. 핵심 로직이나 함수, 클래스를 설명할 때는 반드시 [파일명] 또는 [파일명:라인번호] 형식으로 출처를 명시하세요.
        2. 파일 간의 의존성 및 연결 관계를 아키텍처 관점에서 설명해주세요.
        3. 컨텍스트에 없는 내용을 추측하여 답변하지 말고, 모르는 정보는 모른다고 솔직하게 답변하세요.
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
        당신은 소프트웨어 아키텍트입니다. 다음은 분석 중인 프로젝트의 파일 경로 목록입니다.
        이 파일들을 프로젝트의 도메인, 역할, 또는 기술적 계층(예: UI, Logic, Data, Config, Backend, Frontend 등)에 따라 논리적으로 그룹화하세요.
        
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

    def generate_readme(self, user_inputs: dict = None) -> str:
        if not self.llm:
            return "# README\n\nLLM이 구성되지 않았습니다."
            
        nodes = list(self.graph.nodes())
        file_count = len(nodes)
        
        # 1. 의존성 매니페스트 파일 찾기 (기술 스택 파악용)
        manifest_content = ""
        for path, content in self.files_data.items():
            if any(m in path.lower() for m in ["build.gradle", "package.json", "pom.xml", "requirements.txt", "settings.gradle", "docker-compose.yml"]):
                manifest_content += f"\n--- {path} ---\n{content[:2500]}\n"
        
        # 2. 가장 많이 참조된 Top 5 핵심 파일 코드 스니펫 추출
        in_degrees = dict(self.graph.in_degree())
        top_files = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        top_files_str = "\n".join([f"- {f} (참조됨: {count}회)" for f, count in top_files])
        
        core_files_code = ""
        for f, _ in top_files:
            if f in self.files_data:
                # 각 핵심 파일의 첫 2000자 제공 (클래스 정의, 주요 메서드 파악)
                core_files_code += f"\n--- {f} ---\n{self.files_data[f][:2000]}...\n"
        
        # 3. 디렉토리 구조 생성 (트리 형태)
        import os
        dirs = set()
        for node in nodes:
            dirs.add(os.path.dirname(node))
        dir_tree = "\n".join([f"- {d}/" for d in sorted(list(dirs))[:15]])
        
        # 4. [NEW] 프로젝트 정체성(언어/프레임워크) 자동 추론 로직
        extensions = {}
        framework_hints = set()
        
        for path in self.files_data.keys():
            # 확장자 빈도수 체크
            ext = path.split('.')[-1].lower() if '.' in path else ''
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
                
            # 설정 파일로 프레임워크 힌트 획득
            path_lower = path.lower()
            if "package.json" in path_lower: framework_hints.add("Node.js / NPM")
            if "build.gradle" in path_lower or "settings.gradle" in path_lower: framework_hints.add("Gradle (Android/Spring)")
            if "pom.xml" in path_lower: framework_hints.add("Maven (Java/Spring)")
            if "requirements.txt" in path_lower or "pipfile" in path_lower or "pyproject.toml" in path_lower: framework_hints.add("Python Ecosystem")
            if "dockerfile" in path_lower or "docker-compose" in path_lower: framework_hints.add("Docker Containerization")
            if "cmakelists.txt" in path_lower: framework_hints.add("C/C++ Build System")
            if "tsconfig.json" in path_lower: framework_hints.add("TypeScript")
            if "next.config" in path_lower: framework_hints.add("Next.js")
            if "tailwind.config" in path_lower: framework_hints.add("TailwindCSS")

        # 가장 많이 쓰인 확장자 Top 3
        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:3]
        top_exts_str = ", ".join([f".{ext}({cnt}개)" for ext, cnt in top_exts])
        framework_str = ", ".join(list(framework_hints)) if framework_hints else "특정 프레임워크 추론 불가"

        user_input_context = ""
        if user_inputs and any(user_inputs.values()):
            user_input_context = "\n[👤 사용자 추가 정보 (우선 반영)]\n"
            for k, v in user_inputs.items():
                if v and str(v).strip():
                    user_input_context += f"- {k}: {v}\n"

        context = f"""
        [🤖 프로젝트 정체성 분석 결과]
        - 주 사용 언어/확장자: {top_exts_str}
        - 감지된 환경/프레임워크 힌트: {framework_str}
        {user_input_context}
        
        [📂 프로젝트 구조 및 핵심 데이터]
        1. 전체 파일 수: {file_count}개
        2. 디렉토리 구조 (최상위 일부):
        {dir_tree}
        
        3. 핵심 파일 (많이 참조된 파일):
        {top_files_str}
        
        4. 주요 파일들의 실제 내용 (일부):
        {manifest_content}
        {core_files_code}
        """
        
        system_prompt = SystemMessage(content="""
        당신은 세계 최고의 오픈소스 메인테이너이자 테크니컬 라이터입니다. 
        제공된 코드베이스 분석 결과와 사용자 정보를 바탕으로, GitHub 메인 페이지에 노출될 수 있는 수준의 압도적인 퀄리티의 README.md를 작성하세요.

        [분석 필수 사항]
        - **비즈니스 로직**: 이 프로젝트가 정확히 무엇을 하는지, 어떤 문제를 해결하는지 코드와 사용자 입력으로부터 깊이 있게 파악하세요.
        - **사용자 입력 최우선**: [👤 사용자 추가 정보]가 있다면 해당 내용을 프로젝트 제목, 소개, 주요 기능, 대상 사용자 등에 적극적으로 반영하세요.
        - **아키텍처**: 사용된 디자인 패턴과 프레임워크를 파악하여 명시하세요.
        - **시작하기**: 사용자가 복사-붙여넣기만 하면 바로 실행될 수 있도록 '진짜' 명령어를 작성하세요.

        [레퍼런스: 아래는 당신이 지향해야 할 README 구조입니다. 이와 동일한 수준의 깊이와 디자인을 유지하세요.]
        # 🚀 [프로젝트명]
        > "[한 줄 소개]" <br/>
        > [상세 소개]
        ![Version](...) ![TechStack](...) ...
        ## 📝 목차
        ## 💡 프로젝트 소개
        ## ✨ 주요 기능 (Key Features)
        ## 🛠 기술 스택 (Tech Stack)
        ## 📱 화면 구성 및 사용법 (Usage)
        ## 🚀 시작하기 (Getting Started)
        ## 📂 폴더 구조 (Directory Structure)

        [작성 규칙]
        1. **Overview**: 프로젝트의 가치를 3~5문장으로 깊이 있게 설명하세요.
        2. **Features**: 단순 나열이 아닌, "어떤 기술을 써서 어떻게 동작하는지" 기술적 디테일을 포함하세요.
        3. **Directory Structure**: 이모지를 활용해 프로젝트의 뼈대를 아름답게 그리세요.
        4. **Style**: 볼드체, 인용구(>), 표, 하이라이트 등을 적극적으로 사용하여 읽기 즐거운 문서를 만드세요.

        ---
        응답은 오직 README.md 마크다운 코드만 출력하세요. (백틱 없이 순수 텍스트만)
        """)
        
        user_prompt = HumanMessage(content=context)
        
        response = self.llm.invoke([system_prompt, user_prompt])
        content = response.content.strip()
        
        if "```markdown" in content:
            content = content.split("```markdown")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return content