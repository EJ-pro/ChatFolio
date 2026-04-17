import os
from dotenv import load_dotenv
from parser.github_fetcher import GitHubFetcher
from parser.kotlin_parser import parse_kotlin_code
from graph.graph_builder import DependencyGraphBuilder
from rag.engine import ChatFolioEngine

load_dotenv()

def start_chat():
    token = os.getenv("GITHUB_TOKEN")
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return

    # 1. 데이터 준비 (이전 단계와 동일)
    fetcher = GitHubFetcher(token=token)
    target_repo = "https://github.com/EJ-pro/Collobo-Station" 
    
    print("🤖 코드를 분석하고 뇌(GraphRAG)를 생성 중입니다. 잠시만 기다려주세요...")
    files = fetcher.fetch_repo_files(target_repo)
    kt_files = {p: c for p, c in files.items() if p.endswith(('.kt', '.kts'))}
    
    all_meta = {p: parse_kotlin_code(c) for p, c in kt_files.items()}
    graph = DependencyGraphBuilder().build_graph(all_meta)

    # 2. 엔진 초기화
    engine = ChatFolioEngine(kt_files, graph)
    print("✅ 준비 완료! 프로젝트에 대해 무엇이든 물어보세요. (종료: quit)\n")

    # 3. 채팅 루프
    while True:
        user_input = input("👤 User: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        print("🔍 ChatFolio 분석 중...")
        answer = engine.ask(user_input)
        print(f"\n🚀 AI: {answer}\n")
        print("-" * 30)

if __name__ == "__main__":
    start_chat()