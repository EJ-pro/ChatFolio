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
        당신은 세계 최고 수준의 시니어 테크니컬 라이터이자 오픈소스 메인테이너입니다.
        제공된 프로젝트 코드 스니펫, 디렉토리 구조, 매니페스트를 심층적으로 분석하여,
        누구나 감탄할 만한 [High-Quality GitHub README.md]를 작성하세요.

        [핵심 작성 지침]
        1. 단순한 코드 나열이 아닌, 이 프로젝트가 "왜 만들어졌고", "어떤 비즈니스 로직/문제를 해결하는지"를 코드를 통해 날카롭게 추론하여 작성하세요.
        2. 제공된 템플릿 구조를 완벽하게 유지하되, 내용은 빈약하지 않게 최대한 구체적이고 전문적인 용어로 풍성하게 채우세요.
        3. 마크다운 문법(볼드체, 인용구, 코드블럭, 표, 이모지)을 적극 활용하여 가독성을 극대화하세요.
        4. 사용자가 나중에 수정해야 할 부분은 `[TODO: 설명 입력]` 형태로 명확히 남겨두세요.

        [반드시 지켜야 할 마크다운 템플릿]
        
        <div align="center">
          <h1>🚀 [유추한 프로젝트 공식 명칭]</h1>
          <p><strong>[코드를 분석하여 도출한 프로젝트의 핵심 가치 및 한 줄 소개]</strong></p>
          <p>
            <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version" />
            <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License" />
            <!-- 코드를 보고 유추한 핵심 기술 뱃지 2~3개를 추가로 작성하세요 -->
          </p>
        </div>

        <br/>

        ## 📖 Overview
        [프로젝트의 기획 의도와 해결하고자 하는 문제, 그리고 주요 타겟 유저층을 코드를 바탕으로 논리적으로 추론하여 3~4문장으로 깊이 있게 작성하세요. 프로젝트가 가지는 기술적 챌린지나 특징도 포함하면 좋습니다.]

        ## ✨ Key Features
        [단순 기능 나열이 아닌, 코드 스니펫에서 발견된 핵심 로직을 바탕으로 동작 방식을 구체적으로 설명하세요.]
        - ⚡ **[핵심 기능 1]**: [해당 기능이 코드 상에서 어떻게 구현되었는지 기술적 디테일을 포함해 설명]
        - 🛡️ **[핵심 기능 2]**: [보안, 상태 관리, 데이터 처리 방식 등 코드에서 돋보이는 부분 설명]
        - 🔄 **[핵심 기능 3]**: [사용자 경험(UX), 외부 API 연동, 아키텍처 패턴 등 설명]

        ## 🏗️ Architecture & Tech Stack
        
        ### 🎯 Core Architecture
        [MVVM, Clean Architecture, MVC 등 코드 구조와 주요 클래스들을 보고 유추한 아키텍처 패턴과 그 도입 이유를 전문적으로 설명하세요.]

        ### 🛠️ Technology Stack
        | Category | Technology | Purpose (추론된 사용 목적) |
        | :--- | :--- | :--- |
        | **Frontend/App** | [기술명 유추] | [UI 렌더링, 상태 관리 등 구체적 역할] |
        | **Backend/Core** | [기술명 유추] | [API 통신, 비즈니스 로직 처리 등 구체적 역할] |
        | **Infra/Tools** | [기술명 유추] | [빌드, 배포, 패키지 관리 등 구체적 역할] |

        ## 🚀 Getting Started
        
        ### Prerequisites
        - [유추된 실행 환경 및 요구 버전 1]
        - [유추된 실행 환경 및 요구 버전 2]

        ### Installation & Run
        ```bash
        # 1. 저장소 클론
        $ git clone [TODO: Repository URL]

        # 2. 의존성 설치 및 빌드
        $ [매니페스트 기반으로 유추한 패키지 설치 명령어 (예: npm install / ./gradlew build)]
        
        # 3. 프로젝트 실행
        $ [매니페스트 기반으로 유추한 실행 명령어 (예: npm run dev / ./gradlew run)]
        ```

        ## 📂 Project Structure
        <details>
        <summary><b>핵심 디렉토리 구조 펼쳐보기</b></summary>

        ```text
        📦 [프로젝트명]
         ┣ 📂 [주요폴더1]   # [해당 폴더의 주요 역할과 포함된 핵심 비즈니스 로직 설명]
         ┣ 📂 [주요폴더2]   # [해당 폴더의 주요 역할 설명]
         ┗ 📜 [주요설정파일]
        (제공된 디렉토리 데이터를 바탕으로 중요도가 높은 상위 10개 내외의 구조만 요약해서 작성)
        ```
        </details>

        ## 🤝 Contributing
        [TODO: 기여 가이드, PR 규칙, 연락처 등 입력]

        ---
        코드를 깊이 있게 분석하여 가장 '개발자스러운' 통찰력이 담긴 리드미를 작성해야 합니다.
        응답은 오직 README.md 마크다운 코드(```markdown ... ``` 제외)만 순수 텍스트로 출력하세요. 다른 말은 절대 금지합니다.
        """)
        
        user_prompt = HumanMessage(content=context)
        
        response = self.llm.invoke([system_prompt, user_prompt])
        content = response.content.strip()
        
        if "```markdown" in content:
            content = content.split("```markdown")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return content