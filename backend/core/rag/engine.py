from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
# Chroma 대신 순수 파이썬 인메모리 스토어 사용
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage
from .readme_agent import ReadmeAgent
import json
import networkx as nx
import os

class ChatFolioEngine:
    def __init__(self, files_data, graph, tech_stack=None, provider="groq", model_name=None):
        self.files_data = files_data
        self.graph = graph
        self.tech_stack = tech_stack # {main_language, frameworks, used_parsers, language_distribution}
        self.provider = provider
        self.model_name = model_name
        
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
            separators=["\nclass ", "\ndef ", "\nfn ", "\nfun ", "\nfunc ", "\ninterface ", "\nmodule ", "\n\n", "\n"]
        )
        
        docs = []
        items = self.files_data.items() if isinstance(self.files_data, dict) else self.files_data
        
        for path, content in items:
            chunks = text_splitter.split_text(content)
            for chunk in chunks:
                docs.append({"page_content": chunk, "metadata": {"path": path}})
        
        if not docs:
            return InMemoryVectorStore.from_texts([" "], self.embeddings, metadatas=[{"path": "none"}])

        texts = [d["page_content"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        
        return InMemoryVectorStore.from_texts(texts, self.embeddings, metadatas=metadatas)

    def ask(self, query: str):
        # 1. k값을 늘려 더 풍부한 후보군을 확보 (8 -> 12)
        related_docs = self.vector_db.similarity_search(query, k=12)
        
        sources = []
        visited_nodes = []
        
        # 2. 토큰 예산 관리 (최대 8,000자)
        CONTEXT_BUDGET = 8000
        current_usage = 0
        
        # 2-1. 문서(README)와 코드(Implementation) 분리 및 제한
        readme_chunks = []
        code_chunks = []
        seen_paths = set()
        
        # 실제 파일 데이터(neighbor 등)를 위한 추가 경로 저장
        neighbor_paths = []

        for doc in related_docs:
            path = doc.metadata.get('path', 'unknown')
            filename = os.path.basename(path).lower()
            
            if filename == 'readme.md':
                if len(readme_chunks) < 2:
                    readme_chunks.append(doc)
            else:
                code_chunks.append(doc)
            
            if path not in seen_paths:
                seen_paths.add(path)
                sources.append({"path": path, "reason": "Vector Similarity"})
                if path in self.graph:
                    neighbors = list(self.graph.neighbors(path))
                    for n in neighbors[:2]: 
                        if n not in seen_paths:
                            neighbor_paths.append(n)
                            file_name_short = path.split('/')[-1]
                            sources.append({"path": n, "reason": f"Dependency (from {file_name_short})"})
                        visited_nodes.append({"from": path, "to": n})

        # 3. 계층형 컨텍스트 구성 (예산 내에서)
        context_text = ""
        
        # 3-1. 핵심 코드 청크 먼저 배치 (가장 중요)
        if code_chunks:
            context_text += "\n### [SECTION: TECHNICAL IMPLEMENTATION (Source Code)]\n"
            for doc in code_chunks:
                if current_usage >= CONTEXT_BUDGET: break
                snippet = f"--- File Chunk: {doc.metadata['path']} ---\n{doc.page_content}\n"
                context_text += snippet
                current_usage += len(snippet)

        # 3-2. README 내용 배치 (예산 남을 때만)
        if readme_chunks and current_usage < CONTEXT_BUDGET:
            context_text += "\n### [SECTION: PROJECT OVERVIEW (Documentation)]\n"
            for doc in readme_chunks:
                if current_usage >= CONTEXT_BUDGET: break
                snippet = f"- Source: {doc.metadata['path']}\n{doc.page_content}\n\n"
                context_text += snippet
                current_usage += len(snippet)

        # 3-3. 연관 파일(Neighbor) 배치 - 최소 정보만 (예산 남을 때만)
        if neighbor_paths and current_usage < CONTEXT_BUDGET:
            context_text += "\n### [SECTION: RELATED CONTEXT (Dependencies)]\n"
            for path in neighbor_paths:
                if current_usage >= CONTEXT_BUDGET: break
                if path in self.files_data:
                    # 주변 파일은 아주 짧게 (500자)
                    content = self.files_data[path][:500]
                    snippet = f"\n--- File (Partial): {path} ---\n{content}\n"
                    context_text += snippet
                    current_usage += len(snippet)

        tech_context = ""
        if self.tech_stack:
            tech_context = f"\n[Project Tech Stack]\n- Main Language: {self.tech_stack.get('main_language')}\n- Frameworks: {', '.join(self.tech_stack.get('frameworks', []))}\n- Used Parsers: {', '.join(self.tech_stack.get('used_parsers', []))}\n"

        # 4. 소스 코드 중심의 강력한 시스템 프롬프트
        system_prompt = SystemMessage(content=f"""
        당신은 숙련된 풀스택 소프트웨어 엔지니어이자 코드 아키텍처 전문가입니다. 
        사용자의 질문에 답변할 때 다음 지침을 엄격히 준수하십시오:
        
        1. **코드 최우선 분석 (Code-First Analysis)**: 'DOCUMENTATION' 섹션은 참고용일 뿐입니다. 모든 기술적 질문은 반드시 'SOURCE CODE' 섹션의 실제 코드를 분석하여 답변하십시오. 
        2. **구체적 근거 제시**: 답변 시 핵심 로직이 담긴 함수명, 클래스명, 혹은 특정 코드 패턴을 직접 언급하십시오.
        3. **비판적 분석**: 문서상 설명과 실제 코드가 다르다면, 코드의 구현 상태를 진실로 간주하고 그 차이점을 지적하십시오.
        4. **가독성**: 복잡한 로직은 단계별로 설명하되 기술적 정확성을 유지하십시오.
        
        {tech_context}
        """)
        
        user_prompt = HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {query}")
        response = self.llm.invoke([system_prompt, user_prompt])
        
        return {
            "answer": response.content,
            "sources": sources,
            "graph_trace": visited_nodes
        }

    def _get_cheap_llm(self):
        """가벼운 작업을 위한 보조 모델 (Llama 8B / GPT-4o-mini)을 반환합니다."""
        if self.provider == "groq":
            return ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        elif self.provider == "openai":
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        return self.llm

    def summarize_title(self, query: str) -> str:
        """첫 번째 질문을 기반으로 짧은 채팅방 제목을 생성합니다. (경량 모델 사용)"""
        cheap_llm = self._get_cheap_llm()
        system_prompt = SystemMessage(content="사용자의 질문을 기반으로 3~5단어 내외의 아주 짧은 제목을 작성해줘. 제목만 출력하고 따옴표나 마침표는 생략해.")
        user_prompt = HumanMessage(content=f"Question: {query}")
        
        try:
            response = cheap_llm.invoke([system_prompt, user_prompt])
            return response.content.strip().replace('"', '').replace("'", "")
        except Exception:
            return query[:20] + "..."

    def generate_mermaid(self) -> str:
        if not self.llm:
            return "graph TD\n    A[LLM Not Configured]"
            
        cheap_llm = self._get_cheap_llm()
        nodes = list(self.graph.nodes())
        nodes_str = "\n".join(nodes)
        
        system_prompt = SystemMessage(content="""
        당신은 소프트웨어 아키텍트입니다. 다음은 분석 중인 프로젝트의 파일 경로 목록입니다.
        이 파일들을 프로젝트의 도메인, 역할, 또는 기술적 계층에 따라 논리적으로 그룹화하세요.
        
        [출력 형식 - 반드시 JSON만 출력하세요]
        ```json
        {
          "subgraphs": [
            {
              "name": "Component",
              "nodes": ["path/to/file.ext"]
            }
          ]
        }
        ```
        """)
        
        user_prompt = HumanMessage(content=f"Files:\n{nodes_str}")
        
        try:
            response = cheap_llm.invoke([system_prompt, user_prompt])
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            grouping = json.loads(content)
            
            node_id_map = {node: f"Node_{i}" for i, node in enumerate(nodes)}
            mermaid_lines = ["graph TD"]
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
                
            for node in nodes:
                if node not in used_nodes:
                    node_id = node_id_map[node]
                    display_name = node.split('/')[-1]
                    mermaid_lines.append(f'    {node_id}["{display_name}"]')
            
            for u, v in self.graph.edges():
                if u in node_id_map and v in node_id_map:
                    mermaid_lines.append(f"    {node_id_map[u]} --> {node_id_map[v]}")
            return "\n".join(mermaid_lines)
        except Exception as e:
            print(f"Mermaid generation failed: {e}")
            fallback_lines = ["graph TD"]
            node_id_map = {node: f"N_{i}" for i, node in enumerate(nodes)}
            for node, nid in node_id_map.items():
                fallback_lines.append(f'    {nid}["{node.split("/")[-1]}"]')
            for u, v in self.graph.edges():
                if u in node_id_map and v in node_id_map:
                    fallback_lines.append(f"    {node_id_map[u]} --> {node_id_map[v]}")
            return "\n".join(fallback_lines)

    def generate_readme(self, user_inputs: dict = None, llm=None, provider=None, model_name=None) -> str:
        target_llm = llm if llm else self.llm
        target_provider = provider if provider else self.provider
        target_model = model_name if model_name else self.model_name

        if not target_llm:
            return "# README\n\nLLM이 구성되지 않았습니다."
            
        nodes = list(self.graph.nodes())
        file_count = len(nodes)
        
        # 3-1. 설정 파일(Manifest) 추출 및 최적화
        manifest_content = ""
        README_CONTEXT_BUDGET = 10000
        current_usage = 0
        
        # 중복 방지를 위해 자물쇠 파일보다는 설정 파일 원본을 우선함
        manifest_priority = ["package.json", "build.gradle", "pom.xml", "requirements.txt", "settings.gradle", "docker-compose.yml"]
        skip_files = ["package-lock.json", "yarn.lock", "gradle-wrapper.properties"]
        
        for path, content in self.files_data.items():
            if current_usage >= README_CONTEXT_BUDGET: break
            fname = os.path.basename(path).lower()
            if any(m in fname for m in manifest_priority) and not any(s in fname for s in skip_files):
                # 설정 파일은 800자만 있어도 의존성 파악 가능
                snippet = f"\n--- {path} ---\n{content[:800]}\n"
                manifest_content += snippet
                current_usage += len(snippet)
        
        # 3-2. 핵심 파일 선정 (In-degree 기준)
        in_degrees = dict(self.graph.in_degree())
        top_files = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        top_files_str = "\n".join([f"- {f} (참조됨: {count}회)" for f, count in top_files])
        
        # 3-3. 핵심 코드 본문 추출 (1,000자 캡핑)
        core_files_code = ""
        for f, _ in top_files:
            if current_usage >= README_CONTEXT_BUDGET: break
            if f in self.files_data:
                # 코드 본문은 1,000자면 핵심 로직 파악 가능
                snippet = f"\n--- {f} ---\n{self.files_data[f][:1000]}...\n"
                core_files_code += snippet
                current_usage += len(snippet)
        
        dirs = set()
        for node in nodes:
            dirs.add(os.path.dirname(node))
        dir_tree = "\n".join([f"- {d}/" for d in sorted(list(dirs))[:15]])
        
        extensions = {}
        framework_hints = set()
        for path in self.files_data.keys():
            ext = path.split('.')[-1].lower() if '.' in path else ''
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
            path_lower = path.lower()
            if "package.json" in path_lower: framework_hints.add("Node.js / NPM")
            if "build.gradle" in path_lower or "settings.gradle" in path_lower: framework_hints.add("Gradle (Android/Spring)")
            if "pom.xml" in path_lower: framework_hints.add("Maven (Java/Spring)")
            if "requirements.txt" in path_lower: framework_hints.add("Python Ecosystem")
            if "dockerfile" in path_lower or "docker-compose" in path_lower: framework_hints.add("Docker")
            if "tsconfig.json" in path_lower: framework_hints.add("TypeScript")

        top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:3]
        top_exts_str = ", ".join([f".{ext}({cnt}개)" for ext, cnt in top_exts])
        framework_str = ", ".join(list(framework_hints)) if framework_hints else "특정 프레임워크 추론 불가"

        user_input_context = ""
        if user_inputs and any(user_inputs.values()):
            user_input_context = "\n[👤 사용자 추가 정보]\n"
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
        2. 디렉토리 구조 (최상위 일부): {dir_tree}
        3. 핵심 파일 (많이 참조된 파일): {top_files_str}
        4. 주요 파일들의 실제 내용 (일부):
        {manifest_content}
        {core_files_code}
        """
        
        agent = ReadmeAgent(target_llm, provider=target_provider, model_name=target_model)
        return agent.run(context, user_inputs or {})