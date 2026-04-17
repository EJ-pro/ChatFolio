import os
from dotenv import load_dotenv
from parser.github_fetcher import GitHubFetcher
from parser.kotlin_parser import parse_kotlin_code
from graph.graph_builder import DependencyGraphBuilder

load_dotenv()

def run_poc():
    token = os.getenv("GITHUB_TOKEN")
    fetcher = GitHubFetcher(token=token)
    target_repo = "https://github.com/EJ-pro/Collobo-Station" 

    # 1. 데이터 수집
    files = fetcher.fetch_repo_files(target_repo)
    kt_files = {p: c for p, c in files.items() if p.endswith(('.kt', '.kts'))}
    
    # 2. 모든 파일 파싱 및 메타데이터 저장
    all_meta = {}
    for path, content in kt_files.items():
        all_meta[path] = parse_kotlin_code(content)

    # 3. 그래프 구축
    builder = DependencyGraphBuilder()
    graph = builder.build_graph(all_meta)
    summary = builder.get_summary()

    # 4. 결과 출력
    print("\n" + "="*60)
    print(f"📊 [Project Analysis: {target_repo}]")
    print(f"✅ 분석된 파일 수: {summary['nodes']}개")
    print(f"✅ 연결된 의존성 수: {summary['edges']}개")
    print("="*60)

    print("\n🏆 가장 많이 참조되는 파일 (핵심 모듈):")
    for path, count in summary['top_referenced']:
        file_name = path.split("/")[-1]
        print(f" - {file_name}: {count}번 참조됨")

    print("\n🔗 주요 의존 관계 예시 (일부):")
    for u, v in list(graph.edges())[:10]:
        print(f" {u.split('/')[-1]} ➔ {v.split('/')[-1]}")

if __name__ == "__main__":
    run_poc()