from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEndpoint, HuggingFaceEmbeddings, ChatHuggingFace
# ChromaDB 영구 저장소 사용
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from .readme_agent import ReadmeAgent
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
import json
import networkx as nx
import os
import shutil
import re

class ChatFolioEngine:
    def __init__(self, files_data, graph, project_id=None, tech_stack=None, provider="groq", model_name=None, force_reload=False):
        self.files_data = files_data
        self.graph = graph
        self.project_id = project_id
        self.tech_stack = tech_stack # {main_language, frameworks, used_parsers, language_distribution}
        self.provider = provider
        self.model_name = model_name
        self.force_reload = force_reload
        
        # LLM 초기화
        if provider == "huggingface":
            # HuggingFace 무료 모델 (Qwen 2.5 Coder 기반, 코딩 특화)
            repo_id = model_name or "Qwen/Qwen2.5-Coder-7B-Instruct"
            if "qwen2.5-7b" in repo_id.lower() or "qwen3.6" in repo_id.lower() or "mistral" in repo_id.lower():
                repo_id = "Qwen/Qwen2.5-Coder-7B-Instruct"
            elif "qwen2.5-32b" in repo_id.lower():
                repo_id = "Qwen/Qwen2.5-Coder-32B-Instruct"
                
            hf_llm = HuggingFaceEndpoint(
                repo_id=repo_id,
                max_new_tokens=512,
                temperature=0.1,
                huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN")
            )
            self.llm = ChatHuggingFace(llm=hf_llm)
        else: # Default is groq
            self.llm = ChatGroq(model=model_name or "llama-3.3-70b-versatile", temperature=0)
            
        # 검증용 모델 (항상 GROQ 사용)
        self.verifier_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
            
        # OpenAI 대신 최고성능 무료 임베딩 모델 사용 (BGE-M3)
        print("🚀 [Embeddings] Loading BGE-M3 model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3"
        )
        
        # 1. 벡터 스토어 및 BM25 검색기 구축
        self.vector_db = self._prepare_vector_db()
        self.bm25_retriever = self._prepare_bm25_retriever()

    def _prepare_vector_db(self):
        # 1. 영구 저장 경로 설정
        persist_dir = None
        if self.project_id:
            persist_dir = f"storage/vectors/{self.project_id}"
            
        # 2. 캐시 사용 여부 확인
        if not self.force_reload and persist_dir and os.path.exists(persist_dir) and os.listdir(persist_dir):
            print(f"📦 [Chroma] Loading existing vector DB from {persist_dir}")
            try:
                return Chroma(persist_directory=persist_dir, embedding_function=self.embeddings)
            except Exception as e:
                print(f"⚠️ [Chroma] Failed to load existing DB: {e}. Recreating...")

        # 3. 최신성 보장을 위해 기존 인덱스 강제 삭제 및 새로 생성
        if persist_dir and os.path.exists(persist_dir):
            try:
                shutil.rmtree(persist_dir, ignore_errors=True)
                print(f"🧹 [Chroma] Cleared old vector DB at {persist_dir}")
            except Exception as e:
                print(f"⚠️ [Chroma] Failed to clear old DB: {e}")

        # 디렉토리 미리 생성
        if persist_dir:
            os.makedirs(persist_dir, exist_ok=True)
                
        # 4. 데이터가 없으면 새로 생성
        print("🔨 [Chroma] Creating new vector DB from latest files...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600, 
            chunk_overlap=50,
            separators=["\nclass ", "\ndef ", "\nfn ", "\nfun ", "\nfunc ", "\ninterface ", "\nmodule ", "\n\n", "\n"]
        )
        
        docs = []
        items = self.files_data.items() if isinstance(self.files_data, dict) else self.files_data
        
        for path, content in items:
            chunks = text_splitter.split_text(content)
            current_pos = 0
            for chunk in chunks:
                # 라인 번호 계산 로직 보강 (공백 무시하고 찾기)
                clean_chunk = chunk.strip()
                start_index = content.find(clean_chunk, current_pos)
                if start_index == -1:
                    # 못 찾으면 전체에서 다시 찾기
                    start_index = content.find(clean_chunk)
                    
                if start_index != -1:
                    start_line = content.count('\n', 0, start_index) + 1
                    end_line = start_line + chunk.count('\n')
                    current_pos = start_index + len(chunk)
                    docs.append({"page_content": chunk, "metadata": {"path": path, "start_line": start_line, "end_line": end_line}})
                else:
                    docs.append({"page_content": chunk, "metadata": {"path": path}})
        
        if not docs:
            # 빈 결과 방지
            return Chroma.from_texts([" "], self.embeddings, metadatas=[{"path": "none"}], persist_directory=persist_dir)

        texts = [d["page_content"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        
        try:
            vector_db = Chroma.from_texts(
                texts=texts, 
                embedding=self.embeddings, 
                metadatas=metadatas,
                persist_directory=persist_dir
            )
            print(f"✅ [Chroma] Vector DB created successfully with {len(texts)} chunks.")
            return vector_db
        except Exception as e:
            print(f"❌ [Chroma] Creation failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to in-memory if persistence fails
            return Chroma.from_texts(texts, self.embeddings, metadatas=metadatas)

    def _prepare_bm25_retriever(self):
        """키워드 기반 검색을 위한 BM25 리트리버 준비"""
        print("🔍 [BM25] Initializing keyword search engine...")
        docs = []
        
        items = self.files_data.items() if isinstance(self.files_data, dict) else self.files_data
        for path, content in items:
            if not content or len(content.strip()) < 10: continue
            
            # 파일당 하나의 문서로 간주하거나, 너무 크면 줄 단위로 분할
            lines = content.split('\n')
            # 50줄 단위로 묶어서 문서 생성
            for i in range(0, len(lines), 50):
                chunk = '\n'.join(lines[i:i+50])
                docs.append(Document(
                    page_content=chunk,
                    metadata={"path": path, "start_line": i+1, "end_line": i+len(lines[i:i+50])}
                ))
        
        if not docs:
            docs = [Document(page_content=" ", metadata={"path": "none"})]
            
        return BM25Retriever.from_documents(docs)

    def ask(self, query: str, history: list = None, language: str = "English"):
        # 1. 동적 k 설정 (프로젝트 규모에 비례)
        file_count = len(self.files_data)
        # 작은 프로젝트는 매우 꼼꼼하게(20개), 큰 프로젝트도 충분히(12~15개)
        base_k = 20 if file_count < 50 else (15 if file_count < 200 else 12)
        
        # 2. 하이브리드 검색 (Vector + BM25)
        # 2.1 벡터 검색 (의미 기반)
        print(f"📡 [Hybrid] Searching for: {query}")
        vector_results = self.vector_db.similarity_search(query, k=base_k * 2)
        
        # 2.2 BM25 검색 (키워드 기반)
        bm25_results = self.bm25_retriever.invoke(query)
        bm25_results = bm25_results[:base_k] # 상위 K개만 사용
        
        # 2.3 결과 결합 및 중복 제거
        combined_results = []
        seen_ids = set()
        
        # 벡터 결과와 BM25 결과 결합
        for doc in vector_results + bm25_results:
            # 경로와 내용의 일부를 조합하여 고유 ID 생성
            doc_id = f"{doc.metadata.get('path')}:{doc.page_content[:100]}"
            if doc_id not in seen_ids:
                combined_results.append(doc)
                seen_ids.add(doc_id)

        # 3. LLM 기반 Re-ranking (정밀도 극대화)
        # 검색된 후보들 중 질문과 가장 관련 높은 문서를 선별 (최대 20개 후보 제공)
        candidates = combined_results[:20]
        final_docs = self._rerank_with_llm(query, candidates, top_n=8) # 최종 상위 8개 선택
        
        sources = []
        visited_nodes = []
        
        # 5. 토큰 예산 관리 (최대 12,000자)
        CONTEXT_BUDGET = 12000
        current_usage = 0
        
        # 5-1. 문서(README)와 코드(Implementation) 분리 및 제한
        readme_chunks = []
        code_chunks = []
        seen_paths = set()
        
        neighbor_paths = []

        for doc in final_docs:
            path = doc.metadata.get('path', 'unknown')
            filename = os.path.basename(path).lower()
            start_line = doc.metadata.get('start_line', '?')
            end_line = doc.metadata.get('end_line', '?')
            
            if filename == 'readme.md':
                if len(readme_chunks) < 2:
                    readme_chunks.append(doc)
            else:
                code_chunks.append(doc)
            
            if path not in seen_paths:
                seen_paths.add(path)
                sources.append({
                    "path": path, 
                    "reason": "AI Ranked Context",
                    "lines": f"L{start_line}-L{end_line}"
                })
                if path in self.graph:
                    neighbors = list(self.graph.neighbors(path))
                    # 그래프 기반 검색 고도화: 의존도(in_degree)가 높은 핵심 파일 위주로 정렬
                    neighbors.sort(key=lambda x: self.graph.in_degree(x) if x in self.graph else 0, reverse=True)
                    for n in neighbors[:3]: 
                        if n not in seen_paths:
                            neighbor_paths.append(n)
                            file_name_short = path.split('/')[-1]
                            sources.append({
                                "path": n, 
                                "reason": f"Dependency (from {file_name_short})"
                            })
                        visited_nodes.append({"from": path, "to": n})

        # 6. 계층형 컨텍스트 구성
        context_text = ""
        
        if code_chunks:
            context_text += "\n### [SECTION: TECHNICAL IMPLEMENTATION (Source Code)]\n"
            for doc in code_chunks:
                if current_usage >= CONTEXT_BUDGET: break
                start_line = doc.metadata.get('start_line', '?')
                end_line = doc.metadata.get('end_line', '?')
                snippet = f"--- File Chunk: {doc.metadata['path']} (Lines {start_line}-{end_line}) ---\n{doc.page_content}\n"
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
        # 전체 파일 목록 (최대 500개까지 확장하여 프로젝트 맵 제공)
        all_paths = list(self.files_data.keys())
        priority_paths = [p for p in all_paths if any(x in p.lower() for x in ['src', 'app', 'core', 'lib', 'main', 'api', 'pkg', 'cmd', 'scripts'])]
        other_paths = [p for p in all_paths if p not in priority_paths]
        all_files_list = "\n".join([f"- {p}" for p in (priority_paths + other_paths)[:500]])

        system_prompt = f"""
        You are an elite Software Architect and Code Auditor. 
        Your goal is to provide 100% technically accurate analysis based ONLY on the provided source code.

        [PROJECT BRAIN MAP (Full File Tree)]
        {all_files_list}

        [STRICT OPERATIONAL RULES - READ CAREFULLY]
        1. **NO HALLUCINATION**: Never invent file names, directory structures, or logic that is not present in the 'TECHNICAL IMPLEMENTATION' section.
        2. **STRICT CONTEXTUALITY**: If the answer is not in the provided code snippets, clearly state: "I cannot find the specific implementation of X in the provided context." 
        3. **FILE PATH VERIFICATION**: You must cross-reference every file path you mention with the [PROJECT BRAIN MAP] and the '--- File Chunk: path ---' headers. 
        4. **CRITICAL THINKING**: Analyze the code's intent. Don't just repeat what's in the comments; explain the logic and potential edge cases (e.g., error handling, performance).
        5. **DOMAIN ADAPTATION**: Adapt your tone to the project's archetype (CLI, Web, AI, etc.).

        [STRICT FORMATTING RULES]
        - **Language**: You MUST answer in {language}.
        - **Structure**: Use Markdown headers (###), bullet points (-), and bold text (**bold**).
        - **Spacing**: Use double newlines (\n\n) between sections.

        [MANDATORY ANALYSIS SUMMARY]
        At the end of your response, provide the following summary:
        ### 🔍 Analysis Summary
        - **Keywords**: [3-5 core technical keywords]
        - **Reference Files**: [List exact file paths and line ranges used]
        - **AI Confidence**: [0-100%] (Based on how much of the needed info was in the context)
        - **Trust Level**: [Low / Medium / High] (Low if you had to guess any logic)

        {tech_context}
        """
        
        user_prompt = f"### [SECTION: TECHNICAL IMPLEMENTATION]\n{context_text}\n\n### [USER QUESTION]\n{query}"
        
        messages = [SystemMessage(content=system_prompt)]
        
        # 이전 대화 내역 추가 (컨텍스트 유지)
        if history:
            for msg in history:
                if msg.get('role') == 'user':
                    messages.append(HumanMessage(content=msg.get('content', '')))
                elif msg.get('role') == 'assistant':
                    messages.append(AIMessage(content=msg.get('content', '')))
        
        messages.append(HumanMessage(content=user_prompt))
        
        response = self.llm.invoke(messages)
        
        final_answer = response.content
        
        if self.provider == "huggingface":
            verification_prompt = f"Review and polish this technical answer in {language} for accuracy and readability.\n\nAnswer: {final_answer}"
            verified_response = self.verifier_llm.invoke([
                SystemMessage(content="You are a Technical Verifier."),
                HumanMessage(content=verification_prompt)
            ])
            final_answer = verified_response.content

        # 8. 자가 검증 (Self-Evaluation)
        evaluation = self._evaluate_answer(query, final_answer, context_text)

        return {
            "answer": final_answer,
            "sources": sources,
            "evaluation": evaluation,
            "graph_trace": visited_nodes,
            "usage": response.response_metadata.get("token_usage", {})
        }

    def _evaluate_answer(self, query: str, answer: str, context: str) -> dict:
        """LLM을 사용하여 생성된 답변의 정확성과 신뢰도를 검증합니다."""
        eval_prompt = f"""
        You are a Technical Quality Auditor. Evaluate the 'Answer' based on the 'Context' provided.
        
        [Query]
        {query}
        
        [Context]
        {context}
        
        [Answer]
        {answer}
        
        [Criteria]
        1. **Faithfulness**: Is the answer derived ONLY from the context? (0-100)
        2. **Technical Accuracy**: Are class/function names and logic correct according to the code? (0-100)
        3. **File Path Integrity**: Are ALL mentioned file paths actually present in the 'Context'? (If AI invented a file name, score must be 0)
        
        [Output Format - JSON only]
        {{
            "score": average_score,
            "verdict": "High Trust" | "Medium Trust" | "Low Trust" | "CRITICAL HALLUCINATION",
            "reason": "summary of evaluation (in Korean) - Must mention if file paths were verified",
            "checks": {{
                "faithfulness": 100,
                "accuracy": 100,
                "file_path_verified": true,
                "hallucination_detected": false
            }}
        }}
        """
        try:
            response = self.verifier_llm.invoke([
                SystemMessage(content="You are a strict technical evaluator. Output JSON only."),
                HumanMessage(content=eval_prompt)
            ])
            # JSON 리스트 추출
            import json, re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            print(f"Evaluation failed: {e}")
            
        return {
            "score": 0, 
            "verdict": "Evaluation Failed", 
            "reason": "검증 도중 오류가 발생했습니다.",
            "checks": {"faithfulness": 0, "accuracy": 0, "hallucination_detected": True}
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
        
        system_prompt = f"""
        You are a Senior Software Architect. 
        Analyze the project structure and tech stack to provide a professional architecture review in {language}.
        
        [Strict Formatting Rules]
        1. **Markdown**: Use clear Markdown headers (###), bullet points (-), and dividers (---).
        2. **Spacing**: Ensure double newlines between paragraphs and sections for maximum readability.
        3. **Sections**: Explicitly label sections like "Overall Design", "Data Flow", etc.
        """
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
        3. **Data/Control Flow**: Explain how data or control flows through the system (e.g., Request -> Router -> Controller -> Service -> DB for web apps, or Entry Point -> Config -> Core Logic -> Output for CLI/Scripts).
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

    def generate_pipeline(self, language: str = "English"):
        """프로젝트의 소스 코드를 분석하여 실행 흐름(Pipeline)을 동적으로 생성합니다."""
        # 중요 파일 추출 (중심성 기반)
        try:
            centrality = nx.degree_centrality(self.graph)
            top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
            top_files = [node[0] for node in top_nodes]
        except:
            top_files = list(self.files_data.keys())[:5]
            
        important_snippets = ""
        for path in top_files:
            content = self.files_data.get(path, "")
            if content:
                important_snippets += f"\n- File: {path}\n```\n{content[:800]}\n```\n"

        system_prompt = f"""
        You are a Senior System Architect. 
        Analyze the provided source code snippets to identify the core "Execution Pipeline" (Data/Logic Flow) of this project.
        You must summarize how data flows through this specific system.
        Respond in {language}.
        
        [Output Format - JSON only]
        {{
            "steps": [
                {{
                    "id": "step_id",
                    "title": "Short Step Title",
                    "desc": "Brief description of this stage",
                    "file": "main_file_path.ext",
                    "tech": ["Tech1", "Tech2"],
                    "color": "#HEX_COLOR",
                    "details": {{
                        "actions": ["Action 1", "Action 2", "Action 3"],
                        "payload": {{ "key": "example_data_structure" }}
                    }}
                }}
            ]
        }}
        
        [Rules]
        1. Identify 5 to 8 logical steps representing the core life cycle (e.g., Initialization -> Processing -> Output, or Request -> Auth -> Logic -> Response).
        2. Assign a unique vibrant color to each step (Tailwind-like hex colors).
        3. 'payload' should show a realistic example of the data structure processed at that step.
        4. OUTPUT ONLY RAW JSON.
        """
        
        user_prompt = f"Tech Stack: {json.dumps(self.tech_stack)}\n\nImportant Files Context:\n{important_snippets}"
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            
            import re
            match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            print(f"Pipeline generation failed: {e}")
            
        return {"steps": []}

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