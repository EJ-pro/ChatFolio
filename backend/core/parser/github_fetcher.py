import base64
import os
from github import Github, Auth

class GitHubFetcher:
    def __init__(self, token: str):
        auth = Auth.Token(token)
        self.g = Github(auth=auth)
        # Target file extensions for analysis (text-based source code, config, and docs)
        self.target_extensions = (
            '.kt', '.kts', '.java', '.py', '.js', '.ts', '.tsx', '.jsx', 
            '.cpp', '.h', '.c', '.go', '.rs', '.swift', '.svelte', '.html', '.css',
            '.json', '.yaml', '.yml', '.toml', '.xml', '.properties', '.gradle',
            '.md', '.txt', '.sh', '.dockerfile', 'dockerfile'
        )

    def _is_valid_file(self, file_path: str) -> bool:
        """Check whether the given file path is valid for code analysis. Returns True to collect, False to skip."""
        path_lower = file_path.lower()
        
        # 1. Directory names that must always be excluded (checked anywhere in the path)
        blacklisted_dirs = {
            "/node_modules/", "/venv/", "/.venv/", "/env/", "/__pycache__/",
            "/vendor/", "/.gradle/", "/.m2/", 
            "/build/", "/dist/", "/out/", "/target/", "/bin/", "/obj/",
            "/.idea/", "/.vscode/", "/.history/", "/.next/", "/.nuxt/",
            "/coverage/", "/.pytest_cache/", "/ios/Pods/", "/.expo/",
            "/.svelte-kit/", "/.tox/"
        }
        
        # Prepend '/' to also catch top-level paths returned by the GitHub API
        check_path = f"/{path_lower}"
        if any(b_dir in check_path for b_dir in blacklisted_dirs):
            return False
            
        # 2. Block specific file names that consume excessive tokens
        blacklisted_files = {
            "package-lock.json", "yarn.lock", "pnpm-lock.yaml", 
            "poetry.lock", "gemfile.lock", ".ds_store", "thumbs.db",
            "id_rsa", "id_dsa", ".eslintcache", ".stylelintcache"
        }
        file_name = path_lower.split("/")[-1]
        if file_name in blacklisted_files:
            return False
            
        # 3. Extensions to exclude from analysis (binary, media, compiled, obfuscated)
        blacklisted_exts = (
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
            ".mp4", ".mp3", ".pdf", ".zip", ".tar.gz",
            ".class", ".jar", ".pyc", ".exe", ".dll", ".so", ".o",
            ".min.js", ".min.css", ".sqlite", ".db",
            ".pem", ".key", ".crt", ".keystore", ".log", ".bak", ".swp", ".tmp"
        )
        if path_lower.endswith(blacklisted_exts):
            return False

        return True

    def fetch_repo_files(self, repo_url: str, progress_callback=None):
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        repo = self.g.get_repo(repo_path)
        
        branch = repo.default_branch
        tree = repo.get_git_tree(branch, recursive=True)
        
        # 1. Extension whitelist filter + 2. Directory/filename blacklist filter
        all_blobs = [
            e for e in tree.tree 
            if e.type == "blob" and 
            (e.path.lower().endswith(self.target_extensions) or e.path.lower() == 'dockerfile') and
            self._is_valid_file(e.path)
        ]
        total_files = len(all_blobs)
        
        msg = f"📂 [{repo.full_name}] ({branch}) Scanning... ({total_files} files total)"
        print(msg)
        if progress_callback: progress_callback(msg)

        # Fetch latest commit info
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
                        progress_callback(f"📄 Collected: {element.path}")
                    
                    yield element.path, content
                except Exception as e:
                    error_msg = f"   ❌ Read failed: {element.path} ({e})"
                    print(error_msg)
                    if progress_callback:
                        progress_callback(error_msg)
        
        return commit_info, file_generator()


    def fetch_latest_commit(self, repo_url: str):
        """Fetch only the latest commit hash and message."""
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        repo = self.g.get_repo(repo_path)
        latest_commit = repo.get_commits()[0]
        return {
            "hash": latest_commit.sha,
            "message": latest_commit.commit.message
        }

    def fetch_commit_stats(self, repo_url: str):
        """Collect data for commit timezone analysis."""
        repo_path = repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
        repo = self.g.get_repo(repo_path)
        
        # Extract timezone from the last 100 commits
        commits = repo.get_commits()[:100]
        hours = []
        for commit in commits:
            # commit.commit.author.date is UTC-based; extract hour only
            hours.append(commit.commit.author.date.hour)
            
        return hours