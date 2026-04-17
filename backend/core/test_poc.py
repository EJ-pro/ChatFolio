import os
from dotenv import load_dotenv
from parser.github_fetcher import GitHubFetcher
from parser.ast_parser import parse_python_code

# 환경 변수 로드 (.env 파일에서 GITHUB_TOKEN 가져오기)
load_dotenv()

def run_poc():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠️ .env 파일에 GITHUB_TOKEN을 설정해주세요.")
        return

    fetcher = GitHubFetcher(token=token)
    
    # 테스트할 타겟 레포지토리 (예시로 작은 레포지토리나 본인의 프로젝트 URL을 넣으세요)
    # LangChain 프레임워크의 아주 작은 서브 모듈 구조 등을 테스트하기 좋습니다.
    target_repo = "https://github.com/langchain-ai/langsmith-sdk" 
    
    print(f"📥 [{target_repo}]에서 코드 수집 중...")
    files = fetcher.fetch_repo_files(target_repo)
    print(f"✅ 총 {len(files)}개의 타겟 파일 수집 완료.\n")

    # 추출한 파일 중 .py 파일 3개만 샘플로 AST 파싱 진행
    py_files = {path: content for path, content in files.items() if path.endswith('.py')}
    
    count = 0
    for path, content in py_files.items():
        if count >= 3: # 너무 길어지니 3개만 출력
            break
            
        print(f"🔍 파싱 중: {path}")
        parsed_data = parse_python_code(content)
        
        print(f"  - Imports: {parsed_data.get('imports', [])[:3]} ...") # 3개만 슬라이싱
        print(f"  - Classes: {[c['name'] for c in parsed_data.get('classes', [])]}")
        print(f"  - Functions: {[f['name'] for f in parsed_data.get('functions', [])]}")
        print("-" * 50)
        
        count += 1

if __name__ == "__main__":
    run_poc()