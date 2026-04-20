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

    def fetch_repo_files(self, repo_url: str, progress_callback=None):
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        repo = self.g.get_repo(repo_path)
        
        branch = repo.default_branch
        tree = repo.get_git_tree(branch, recursive=True)
        
        all_blobs = [e for e in tree.tree if e.type == "blob" and (e.path.lower().endswith(self.target_extensions) or e.path.lower() == 'dockerfile')]
        total_files = len(all_blobs)
        
        msg = f"📂 [{repo.full_name}] ({branch}) 스캔 중... (총 {total_files}개 파일)"
        print(msg)
        if progress_callback: progress_callback(msg)

        # 최신 커밋 정보 가져오기
        latest_commit = repo.get_commits()[0]
        commit_info = {
            "hash": latest_commit.sha,
            "message": latest_commit.commit.message,
            "total_files": total_files
        }
        
        def file_generator():
            for i, element in enumerate(all_blobs):
                try:
                    blob = repo.get_git_blob(element.sha)
                    content = base64.b64decode(blob.content).decode('utf-8', errors='ignore')
                    
                    if progress_callback:
                        progress = int(((i + 1) / total_files) * 100)
                        progress_callback(f"PROGRESS:{progress}")
                        progress_callback(f"📄 수집 완료: {element.path}")
                    
                    yield element.path, content
                except Exception as e:
                    error_msg = f"   ❌ 읽기 실패: {element.path} ({e})"
                    print(error_msg)
                    if progress_callback:
                        progress_callback(error_msg)
        
        return commit_info, file_generator()


    def fetch_latest_commit(self, repo_url: str):
        """최신 커밋 해시와 메시지만 가져옴"""
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        repo = self.g.get_repo(repo_path)
        latest_commit = repo.get_commits()[0]
        return {
            "hash": latest_commit.sha,
            "message": latest_commit.commit.message
        }

    def fetch_commit_stats(self, repo_url: str):
        """커밋 시간대 분석을 위한 데이터 수집"""
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        repo = self.g.get_repo(repo_path)
        
        # 최근 100개 커밋의 시간대 추출
        commits = repo.get_commits()[:100]
        hours = []
        for commit in commits:
            # commit.commit.author.date는 UTC 기준
            # 한국 시간으로 보정하려면 +9시간
            # 여기서는 간단히 시간대만 추출
            hours.append(commit.commit.author.date.hour)
            
        return hours