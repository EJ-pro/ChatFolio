import os
from dotenv import load_dotenv
from parser.github_fetcher import GitHubFetcher
from parser.kotlin_parser import parse_kotlin_code
from graph.graph_builder import DependencyGraphBuilder
from rag.engine import ChatFolioEngine

load_dotenv()

def start_chat():
    token = os.getenv("GITHUB_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("⚠️ .env 파일에 OPENAI_API_KEY가 없습니다.")
        return

    print("🚀 [1단계] GitHub에서 코드 수집 중...")
    fetcher = GitHubFetcher(token=token)
    target_repo = "https://github.com/EJ-pro/Collobo-Station" 
    
    files = fetcher.fetch_repo_files(target_repo)
    kt_files = {p: c for p, c in files.items() if p.endswith(('.kt', '.kts'))}
    print(f"✅ 코틀린 파일 총 {len(kt_files)}개 수집 완료.\n")

    if len(kt_files) == 0:
        print("❌ 분석할 코틀린 파일이 없습니다. 종료합니다.")
        return

    print("🚀 [2단계] AST 분석 및 그래프 지식 지도 구축 중...")
    all_meta = {p: parse_kotlin_code(c) for p, c in kt_files.items()}
    graph = DependencyGraphBuilder().build_graph(all_meta)
    print(f"✅ 그래프 구축 완료 (노드: {graph.number_of_nodes()}개, 엣지: {graph.number_of_edges()}개)\n")

    print("🚀 [3단계] OpenAI 임베딩 및 ChromaDB 벡터 스토어 구축 중... (⏳ 여기서 10~30초 이상 걸릴 수 있습니다)")
    try:
        engine = ChatFolioEngine(kt_files, graph)
        print("✅ DB 구축 완료!\n")
    except Exception as e:
        print(f"\n❌ [치명적 오류] 엔진 초기화 실패: {e}")
        print("-> OpenAI API 키가 만료되었거나, ChromaDB 권한 문제일 수 있습니다.")
        return

    print("=" * 50)
    print("🎉 ChatFolio 준비 완료! 프로젝트에 대해 무엇이든 물어보세요. (종료: q)")
    print("=" * 50)

    while True:
        user_input = input("\n👤 User: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
            
        print("🔍 AI가 코드의 맥락을 추적 중입니다...")
        try:
            answer = engine.ask(user_input)
            
            # 구조화된 응답 출력 (이전 단계에서 수정한 경우)
            if isinstance(answer, dict):
                print(f"\n🚀 AI: {answer['answer']}\n")
                print("🔗 [참고한 파일 흐름]")
                for src in answer.get("sources", []):
                    print(f"   - {src['path']} ({src['reason']})")
            else:
                print(f"\n🚀 AI: {answer}\n")
                
        except Exception as e:
            print(f"\n❌ 답변 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    start_chat()