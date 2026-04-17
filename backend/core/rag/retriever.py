from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

class ChatFolioRetriever:
    def __init__(self, files_data, graph):
        self.embeddings = OpenAIEmbeddings()
        self.graph = graph
        # 1. 벡터 스토어 구축 (코드 본문 저장)
        self.vector_db = Chroma.from_texts(
            texts=list(files_data.values()),
            metadatas=[{"path": p} for p in files_data.keys()],
            embedding=self.embeddings
        )

    def search_with_context(self, query):
        # 1. 질문과 관련된 핵심 파일 찾기 (Vector Search)
        initial_docs = self.vector_db.similarity_search(query, k=2)
        
        # 2. 그래프를 통해 연관된 '이웃' 파일들 찾아내기 (Graph Search)
        context_files = []
        for doc in initial_docs:
            path = doc.metadata['path']
            context_files.append(path)
            # 그래프에서 이 파일이 참조하거나, 이 파일을 참조하는 녀석들 추가
            neighbors = list(self.graph.neighbors(path)) if path in self.graph else []
            context_files.extend(neighbors[:2]) # 너무 많으면 요약이 힘드니 2개만
            
        return list(set(context_files)) # 중복 제거된 연관 파일 리스트