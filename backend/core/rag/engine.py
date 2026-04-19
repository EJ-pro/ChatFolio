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
        당신은 탑티어 시니어 테크니컬 라이터입니다.
        제공된 프로젝트 코드 스니펫과 구조를 바탕으로 GitHub README.md를 마크다운으로 작성하세요.

        [스타일: Standard Professional]
        사용자가 제공한 마크다운 템플릿 구조를 정확히 따르는 표준적인 실리콘밸리 오픈소스 스타일.
        
        [반드시 지켜야 할 마크다운 구조]
        아래 구조를 100% 동일하게 따르되, 괄호 [] 안의 내용이나 기술 스택, 프로젝트 이름, 폴더 구조 등은 제공된 코드와 데이터를 바탕으로 알맞게 채워 넣으세요.
        사용자가 직접 스크린샷이나 링크 등을 넣어야 하는 부분은 "[직접 입력해야 합니다]"와 같이 명시하세요.

        # 🚀 [프로젝트명 유추]
        > "[한 줄 소개 유추]" <br/>
        > [추가 소개 유추]

        ![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
        (이외에 사용된 핵심 기술 스택 뱃지 2~3개 추가)
        ![License](https://img.shields.io/badge/license-MIT-green.svg)

        <br/>

        ## 📝 목차
        1. [프로젝트 소개](#-프로젝트-소개)
        2. [주요 기능](#-주요-기능-key-features)
        3. [기술 스택](#-기술-스택-tech-stack)
        4. [화면 구성 및 사용법](#-화면-구성-및-사용법-usage)
        5. [시작하기](#-시작하기-getting-started)
        6. [폴더 구조](#-폴더-구조-directory-structure)

        <br/>

        ## 💡 프로젝트 소개
        기존의 프로젝트들이 가진 [유추한 문제점/불편함]을 해결하기 위해 기획되었습니다. 
        [프로젝트 목적 상세 작성]

        <br/>

        ## ✨ 주요 기능 (Key Features)
        (제공된 핵심 파일 스니펫을 분석하여 3~4가지 주요 기능 구체적 작성)
        - ⚡ **[기능명]:** [기능 상세 설명]
        - 🎨 **[기능명]:** [기능 상세 설명]
        - 🔒 **[기능명]:** [기능 상세 설명]
        - 📊 **[기능명]:** [기능 상세 설명]

        <br/>

        ## 🛠 기술 스택 (Tech Stack)
        (매니페스트 파일을 기반으로 정확히 분류하여 아래 형식을 유지하세요)
        ### Frontend
        - **Framework:** [React, Kotlin 등 유추]
        - **Styling:** [TailwindCSS, XML 등 유추]
        - **State Management:** [Zustand, ViewModel 등 유추]

        ### Backend
        - **Framework:** [FastAPI, Spring 등 유추]
        - **Database:** [PostgreSQL, MySQL 등 유추]
        - **Real-time/Core:** [WebSockets, Firebase 등 유추]

        ### Infra & Tools
        - **Deployment:** [Docker, AWS 등 유추]
        - **Version Control:** [Git, Github Actions 등 유추]

        <br/>

        ## 📱 화면 구성 및 사용법 (Usage)
        > 💡 실제 구현된 화면 캡처나 GIF(움짤)를 추가하면 신뢰도가 대폭 상승합니다.

        | 메인 대시보드 | 상세 화면 |
        | :---: | :---: |
        | <img src="https://via.placeholder.com/400x250.png?text=Screenshot+1" width="400"/> | <img src="https://via.placeholder.com/400x250.png?text=Screenshot+2" width="400"/> |
        | [메인 화면 설명 - 직접 입력해야 합니다] | [상세 화면 설명 - 직접 입력해야 합니다] |

        <br/>

        ## 🚀 시작하기 (Getting Started)
        프로젝트를 로컬에서 직접 실행해보기 위한 가이드입니다.

        ### 1. 요구 사항 (Prerequisites)
        - [필요한 언어/프레임워크 및 버전 명시 1]
        - [필요한 언어/프레임워크 및 버전 명시 2]

        ### 2. 설치 및 실행 (Installation)
        ```bash
        # 1. 저장소 클론
        $ git clone [저장소 링크 - 직접 입력해야 합니다]

        # 2. 패키지 설치 및 실행 (반드시 한 줄에 하나의 명령어만 작성하세요)
        $ [패키지 설치 명령어 유추]
        $ [실행 명령어 유추]
        ```

        <br/>

        ## 📂 폴더 구조 (Directory Structure)
        ```text
        📦 [프로젝트명]
         ┣ 📂 [폴더명]
         ┃ ┣ 📂 [서브폴더명]   # [역할 설명]
         ┃ ┗ 📜 [파일명]
         ┗ 📜 README.md
        (제공된 디렉토리 데이터를 바탕으로 위와 같은 이모지 트리 형태로 작성)
        ```

        <br/>

        ## 👨‍💻 팀원 및 기여 (Contact)
        [팀원 이름 - 직접 입력해야 합니다] - [역할] - [Github 링크]

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