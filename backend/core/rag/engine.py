from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEndpoint, HuggingFaceEmbeddings
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
        if provider == "huggingface":
            # HuggingFace 무료 모델 (예: Mistral-7B, Llama-3-8B-Instruct)
            # HUGGINGFACEHUB_API_TOKEN 환경 변수 필요
            repo_id = model_name or "mistralai/Mistral-7B-Instruct-v0.2"
            self.llm = HuggingFaceEndpoint(
                repo_id=repo_id,
                max_new_tokens=512,
                temperature=0.1,
                huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
            )
        else: # Default is groq
            self.llm = ChatGroq(model=model_name or "llama-3.3-70b-versatile", temperature=0)
            
        # 검증용 모델 (항상 GROQ 사용)
        self.verifier_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
            
        # OpenAI 대신 무료 임베딩 모델 사용 (all-MiniLM-L6-v2)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
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

    def ask(self, query: str, language: str = "English"):
        # 1. 동적 k 설정 (프로젝트 규모에 비례)
        file_count = len(self.files_data)
        # 작은 프로젝트는 꼼꼼하게(15개), 큰 프로젝트는 노이즈 최소화(8개)
        base_k = 15 if file_count < 50 else (10 if file_count < 200 else 8)
        
        # 2. 유사도 기반 후보군 검색 (2배수 추출)
        # similarity_search_with_score는 (Document, Score) 튜플을 반환
        docs_with_scores = self.vector_db.similarity_search_with_score(query, k=base_k * 2)
        
        # 3. 임계값(Threshold) 필터링 (너무 동떨어진 문맥 제거)
        # OpenAI/Chroma 기준 거리가 너무 멀면(유사도가 낮으면) 제외
        # 참고: 사용 모델/엔진에 따라 스코어 임계값 조정 필요
        filtered_docs = [doc for doc, score in docs_with_scores if score < 0.6] # 0.0에 가까울수록 유사함 (L2 distance)
        
        # 4. LLM 기반 지능형 리랭킹 (Self-Reranking)
        # 단순 검색 결과 중 질문에 진짜 답할 수 있는 것만 골라냄
        final_docs = self._rerank_with_llm(query, filtered_docs, top_n=base_k)
        
        sources = []
        visited_nodes = []
        
        # 5. 토큰 예산 관리 (최대 10,000자)
        CONTEXT_BUDGET = 10000
        current_usage = 0
        
        # 5-1. 문서(README)와 코드(Implementation) 분리 및 제한
        readme_chunks = []
        code_chunks = []
        seen_paths = set()
        
        neighbor_paths = []

        for doc in final_docs:
            path = doc.metadata.get('path', 'unknown')
            filename = os.path.basename(path).lower()
            
            if filename == 'readme.md':
                if len(readme_chunks) < 2:
                    readme_chunks.append(doc)
            else:
                code_chunks.append(doc)
            
            if path not in seen_paths:
                seen_paths.add(path)
                sources.append({"path": path, "reason": "AI Ranked Context"})
                if path in self.graph:
                    neighbors = list(self.graph.neighbors(path))
                    for n in neighbors[:2]: 
                        if n not in seen_paths:
                            neighbor_paths.append(n)
                            file_name_short = path.split('/')[-1]
                            sources.append({"path": n, "reason": f"Dependency (from {file_name_short})"})
                        visited_nodes.append({"from": path, "to": n})

        # 6. 계층형 컨텍스트 구성
        context_text = ""
        
        if code_chunks:
            context_text += "\n### [SECTION: TECHNICAL IMPLEMENTATION (Source Code)]\n"
            for doc in code_chunks:
                if current_usage >= CONTEXT_BUDGET: break
                snippet = f"--- File Chunk: {doc.metadata['path']} ---\n{doc.page_content}\n"
                context_text += snippet
                current_usage += len(snippet)

        if readme_chunks and current_usage < CONTEXT_BUDGET:
            context_text += "\n### [SECTION: PROJECT OVERVIEW (Documentation)]\n"
            for doc in readme_chunks:
                if current_usage >= CONTEXT_BUDGET: break
                snippet = f"- Source: {doc.metadata['path']}\n{doc.page_content}\n\n"
                context_text += snippet
                current_usage += len(snippet)

        if neighbor_paths and current_usage < CONTEXT_BUDGET:
            context_text += "\n### [SECTION: RELATED CONTEXT (Dependencies)]\n"
            for path in neighbor_paths:
                if current_usage >= CONTEXT_BUDGET: break
                if path in self.files_data:
                    content = self.files_data[path][:500]
                    snippet = f"\n--- File (Partial): {path} ---\n{content}\n"
                    context_text += snippet
                    current_usage += len(snippet)

        tech_context = ""
        if self.tech_stack:
            tech_context = f"\n[Project Tech Stack]\n- Main Language: {self.tech_stack.get('main_language')}\n- Frameworks: {', '.join(self.tech_stack.get('frameworks', []))}\n"

        # 7. 소스 코드 중심의 시스템 프롬프트
        system_prompt = f"""
        You are an experienced full-stack software engineer and code architecture expert.
        Analyze the 'TECHNICAL IMPLEMENTATION' section carefully to answer the user's question.
        
        1. **Code-First**: Prioritize actual code implementation over general documentation.
        2. **Evidence**: Quote specific class names, function names, or file paths.
        3. **Clarity**: Explain logic step-by-step.
        4. **Language**: Answer in {language}.
        
        {tech_context}
        """
        
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        final_answer = response.content
        
        if self.provider == "huggingface":
            verification_prompt = f"Review and polish this technical answer in {language} for accuracy and readability.\n\nAnswer: {final_answer}"
            verified_response = self.verifier_llm.invoke([
                SystemMessage(content="You are a Technical Verifier."),
                HumanMessage(content=verification_prompt)
            ])
            final_answer = verified_response.content

        return {
            "answer": final_answer,
            "sources": sources,
            "graph_trace": visited_nodes,
            "usage": response.response_metadata.get("token_usage", {})
        }

    def _rerank_with_llm(self, query: str, docs: list, top_n: int) -> list:
        """가벼운 LLM을 사용하여 검색된 후보군 중 질문과 가장 관련 있는 문서를 선별합니다."""
        if not docs: return []
        if len(docs) <= top_n: return docs
        
        cheap_llm = self._get_cheap_llm()
        
        # 각 문서의 관련성을 평가하기 위한 콤팩트한 리스트 작성
        doc_list_str = ""
        for i, doc in enumerate(docs):
            content_preview = doc.page_content[:300].replace("\n", " ")
            doc_list_str += f"[{i}] Path: {doc.metadata.get('path')}\nContent: {content_preview}\n\n"
            
        rerank_prompt = f"""
        Analyze the following code snippets and select the top {top_n} most relevant snippets that can help answer the question: "{query}".
        
        [Candidates]
        {doc_list_str}
        
        [Instruction]
        Respond with only a JSON list of indices. Example: [0, 2, 5]
        """
        
        try:
            response = cheap_llm.invoke([
                SystemMessage(content="You are a Technical Re-ranker. Select only the most relevant code indices."),
                HumanMessage(content=rerank_prompt)
            ])
            
            # JSON 리스트 추출
            import json, re
            match = re.search(r'\[.*\]', response.content)
            if match:
                indices = json.loads(match.group())
                return [docs[i] for i in indices if i < len(docs)][:top_n]
        except Exception as e:
            print(f"Re-ranking failed: {e}")
            
        return docs[:top_n]

    def analyze_architecture(self, language: str = "English"):
        """프로젝트 그래프와 테크 스택을 기반으로 아키텍처 분석 리포트 생성"""
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()
        
        # 중요도 높은 파일 (Centrality)
        try:
            centrality = nx.degree_centrality(self.graph)
            top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            top_files = [node[0] for node in top_nodes]
        except:
            top_files = []
            
        # 파일 내용 일부 가져오기 (가장 중요한 파일들)
        important_snippets = ""
        for path in top_files:
            content = self.files_data.get(path, "")
            if content:
                # 첫 1000자 정도
                important_snippets += f"\n- File: {path}\n```\n{content[:1000]}\n```\n"
        
        system_prompt = f"You are a Senior Software Architect. Analyze the project structure and tech stack to provide a professional architecture review in {language}."
        user_prompt = f"""
        [Project Statistics]
        - Total Files: {node_count}
        - Total Dependencies: {edge_count}
        - Detected Tech Stack: {json.dumps(self.tech_stack, ensure_ascii=False) if self.tech_stack else "Unknown"}
        
        [Important Files (Top Centrality)]:
        {', '.join(top_files)}
        
        [Source Code Snippets of Key Files]:
        {important_snippets}
        
        Please provide a detailed architecture analysis in {language} covering:
        1. **Overall Design Pattern**: Identify the main structural pattern (e.g., MVC, Layered Architecture, Hexagonal, Clean Architecture, etc.) based on the file names and dependencies.
        2. **Component Roles**: Explain the roles of the 'Important Files' listed above and how they serve as the project's backbone.
        3. **Data/Control Flow**: Explain how data or control flows through the system (e.g., Request -> Router -> Controller -> Service -> DB).
        4. **Architectural Evaluation**: Mention strengths (e.g., good modularity) and potential risks (e.g., circular dependencies, tight coupling in specific areas).
        
        Format the output nicely using Markdown with clear headings.
        """
        
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        return {
            "analysis": response.content,
            "usage": response.response_metadata.get("token_usage", {})
        }

    def _get_cheap_llm(self):
        """가벼운 작업을 위한 보조 모델 (Llama 8B)을 반환합니다."""
        if self.provider == "groq":
            return ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        return self.llm

    def summarize_title(self, query: str) -> str:
        """첫 번째 질문을 기반으로 짧은 채팅방 제목을 생성합니다. (경량 모델 사용)"""
        cheap_llm = self._get_cheap_llm()
        system_prompt = SystemMessage(content="Create a very short title of about 3~5 words based on the user's question. Output only the title without quotes or periods.")
        user_prompt = HumanMessage(content=f"Question: {query}")
        
        try:
            response = cheap_llm.invoke([system_prompt, user_prompt])
            return {
                "title": response.content.strip().replace('"', '').replace("'", ""),
                "usage": response.response_metadata.get("token_usage", {})
            }
        except Exception:
            return query[:20] + "..."

    def generate_mermaid(self) -> str:
        if not self.llm:
            return "graph TD\n    A[LLM Not Configured]"
            
        cheap_llm = self._get_cheap_llm()
        nodes = list(self.graph.nodes())
        nodes_str = "\n".join(nodes)
        
        system_prompt = SystemMessage(content="""
        You are a software architect. The following is a list of file paths for the project under analysis.
        Logically group these files based on the project's domain, role, or technical layer.
        
        [Output Format - Output JSON only]
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

    def generate_readme(self, user_inputs: dict = None, llm=None, provider=None, model_name=None, languages=["English"]) -> str:
        target_llm = llm if llm else self.llm
        target_provider = provider if provider else self.provider
        target_model = model_name if model_name else self.model_name

        if not target_llm:
            return "# README\n\nLLM is not configured."
            
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
        framework_str = ", ".join(list(framework_hints)) if framework_hints else "Specific framework could not be inferred"

        user_input_context = ""
        if user_inputs and any(user_inputs.values()):
            user_input_context = "\n[👤 사용자 추가 정보]\n"
            for k, v in user_inputs.items():
                if v and str(v).strip():
                    user_input_context += f"- {k}: {v}\n"

        context = f"""
        [🤖 프로젝트 정체성 분석 결과]
        - Main Language/Extension: {top_exts_str}
        - Detected Env/Framework Hints: {framework_str}
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
        return agent.run(context, user_inputs or {}, languages=languages)