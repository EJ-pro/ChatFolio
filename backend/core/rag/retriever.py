from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

class ChatFolioRetriever:
    def __init__(self, files_data, graph):
        self.embeddings = OpenAIEmbeddings()
        self.graph = graph
        # 1. Build vector store (store code body)
        self.vector_db = Chroma.from_texts(
            texts=list(files_data.values()),
            metadatas=[{"path": p} for p in files_data.keys()],
            embedding=self.embeddings
        )

    def search_with_context(self, query):
        # 1. Find core files related to the question (Vector Search)
        initial_docs = self.vector_db.similarity_search(query, k=2)
        
        # 2. Find related 'neighbor' files via the graph (Graph Search)
        context_files = []
        for doc in initial_docs:
            path = doc.metadata['path']
            context_files.append(path)
            # Add files that this file references or that reference this file from the graph
            neighbors = list(self.graph.neighbors(path)) if path in self.graph else []
            context_files.extend(neighbors[:2]) # Limit to 2 to keep summarization manageable
            
        return list(set(context_files)) # Deduplicated list of related files