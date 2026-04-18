from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# Chroma 대신 순수 파이썬 인메모리 스토어 사용
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage

class ChatFolioEngine:
    def __init__(self, files_data, graph):
        self.files_data = files_data
        self.graph = graph           
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
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