from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage
import os

class ChatFolioEngine:
    def __init__(self, files_data, graph):
        self.files_data = files_data # {path: content}
        self.graph = graph           # NetworkX DiGraph
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.embeddings = OpenAIEmbeddings()
        
        # 1. 벡터 스토어 구축
        self.vector_db = self._prepare_vector_db()

    def _prepare_vector_db(self):
        # 코드를 의미 있는 단위로 쪼개기 (함수/클래스 단위 지향)
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
        
        return Chroma.from_texts(texts, self.embeddings, metadatas=metadatas)

    def ask(self, query: str):
        # 2. 관련 파일 검색 (Vector + Graph)
        related_docs = self.vector_db.similarity_search(query, k=3)
        
        # 그래프를 통해 연관된 이웃 파일 경로 추가 추출
        context_paths = set()
        for doc in related_docs:
            path = doc.metadata['path']
            context_paths.add(path)
            # 그래프 상의 이웃(의존성) 추가
            if path in self.graph:
                neighbors = list(self.graph.neighbors(path))
                context_paths.update(neighbors[:2]) # 관련 파일당 최대 2개씩 추가

        # 3. 컨텍스트 구성
        context_text = ""
        for path in context_paths:
            if path in self.files_data:
                context_text += f"\n--- File: {path} ---\n{self.files_data[path][:2000]}\n"

        # 4. LLM 답변 생성
        system_prompt = SystemMessage(content=f"""
        당신은 숙련된 안드로이드 개발자이자 코드 분석가입니다. 
        주어진 Kotlin 코드베이스 컨텍스트를 바탕으로 사용자의 질문에 답변하세요.
        답변 시에는 반드시 관련 파일명과 핵심 로직을 언급하세요. 
        만약 모르는 내용이라면 추측하지 말고 모른다고 답하세요.
        """)
        
        user_prompt = HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {query}")
        
        response = self.llm.invoke([system_prompt, user_prompt])
        return response.content