import base64
import os
from github import Github, Auth

class GitHubFetcher:
    def __init__(self, token: str):
        auth = Auth.Token(token)
        self.g = Github(auth=auth)
        # 분석 대상 확장자 정의
        # 분석 대상 확장자 정의 (텍스트 기반의 소스코드, 설정, 문서)
        self.target_extensions = (
            '.kt', '.kts', '.java', '.py', '.js', '.ts', '.tsx', '.jsx', 
            '.cpp', '.h', '.c', '.go', '.rs', '.swift', '.svelte', '.html', '.css',
            '.json', '.yaml', '.yml', '.toml', '.xml', '.properties', '.gradle',
            '.md', '.txt', '.sh', '.dockerfile', 'dockerfile'
        )

    def fetch_repo_files(self, repo_url: str) -> dict:
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        repo = self.g.get_repo(repo_path)
        
        branch = repo.default_branch
        tree = repo.get_git_tree(branch, recursive=True)
        
        files_data = {}
        print(f"📂 [{repo.full_name}] ({branch}) 스캔 중...")

        for element in tree.tree:
            if element.type == "blob":
                # 소문자로 변환하여 확장자 체크
                if element.path.lower().endswith(self.target_extensions):
                    print(f"   ✅ 수집됨: {element.path}")
                    try:
                        blob = repo.get_git_blob(element.sha)
                        content = base64.b64decode(blob.content).decode('utf-8', errors='ignore')
                        files_data[element.path] = content
                    except Exception as e:
                        print(f"   ❌ 읽기 실패: {element.path} ({e})")
        
        return files_data