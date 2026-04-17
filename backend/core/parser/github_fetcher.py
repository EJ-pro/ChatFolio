from github import Github
from github.Repository import Repository
import base64
import os

class GitHubFetcher:
    def __init__(self, token: str = None):
        """
        GitHub API 클라이언트 초기화. Token이 없으면 익명으로 제한적인 호출만 가능.
        """
        self.g = Github(token)
        self.target_extensions = {'.py', '.md', '.txt'} # PoC 타겟 확장자

    def fetch_repo_files(self, repo_url: str) -> dict:
        """
        주어진 레포지토리 URL에서 분석 대상 파일들의 경로와 내용을 딕셔너리로 반환합니다.
        """
        # URL에서 "owner/repo" 형태 추출 (예: https://github.com/ej-pro/chatfolio -> ej-pro/chatfolio)
        repo_path = repo_url.replace("https://github.com/", "").strip("/")
        repo: Repository = self.g.get_repo(repo_path)
        
        # 레포지토리 최상단 트리부터 재귀적으로 탐색
        tree = repo.get_git_tree("HEAD", recursive=True)
        
        files_data = {}
        for element in tree.tree:
            # 파일이 아니거나(blob 아님), 타겟 확장자가 아니면 스킵
            if element.type != "blob":
                continue
                
            _, ext = os.path.splitext(element.path)
            if ext in self.target_extensions:
                # 파일 내용 가져오기 (base64 디코딩)
                blob = repo.get_git_blob(element.sha)
                content = base64.b64decode(blob.content).decode('utf-8', errors='ignore')
                files_data[element.path] = content
                
        return files_data