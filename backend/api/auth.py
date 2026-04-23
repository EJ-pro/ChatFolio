import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi_sso.sso.github import GithubSSO
from github import Github, Auth
from sqlalchemy import func

from database.database import get_db
from database.models import User, Project, GeneratedReadme, ProjectFile, ChatSession
from core.parser.github_fetcher import GitHubFetcher

from core.rag.engine import ChatFolioEngine

router = APIRouter(prefix="/auth", tags=["auth"])

# Load OAuth credentials from environment variables
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_if_not_set")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

# Initialize SSO object (Redirect URI points to the backend callback, not the frontend)
github_sso = GithubSSO(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri="http://localhost:8000/auth/github/callback",
    allow_insecure_http=True, # Allow HTTP in development environment
    scope=["user:email", "repo"] # Add private repository access scope
)

# JWT creation utility
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Validate the currently logged-in user (Dependency)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token validation failed.")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

# Common social login callback processing logic
async def process_sso_login(sso_user, provider: str, db: Session, github_username: str = None, github_token: str = None):
    # Look up existing user by email
    user = db.query(User).filter(User.email == sso_user.email).first()

    if not user:
        # Create a new user if not found
        user = User(
            provider=provider,
            email=sso_user.email,
            name=sso_user.display_name or sso_user.email.split('@')[0],
            avatar_url=sso_user.picture,
            github_username=github_username,
            github_token=github_token
        )
        db.add(user)
    else:
        # Update user information
        user.name = sso_user.display_name or user.name
        user.avatar_url = sso_user.picture or user.avatar_url
        if github_username:
            user.github_username = github_username
        if github_token:
            user.github_token = github_token
    
    db.commit()
    db.refresh(user)
    
    # Issue JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    # Redirect to frontend with token
    frontend_url = f"http://localhost/auth/callback?token={access_token}"
    return RedirectResponse(url=frontend_url)

# Retrieve current user information
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "github_username": current_user.github_username,
        "avatar_url": current_user.avatar_url,
        "provider": current_user.provider,
        "country": current_user.country,
        "job": current_user.job
    }

# Retrieve user profile page information
@router.get("/profile/{username}")
async def get_user_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.github_username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Fetch only completed project data
    projects = db.query(Project).filter(Project.user_id == user.id, Project.status == "COMPLETED").all()

    # Skill statistics (using GitHub API Languages)
    lang_stats = {}
    token = user.github_token or os.getenv("GITHUB_TOKEN")
    
    if token and projects:
        try:
            auth = Auth.Token(token)
            g = Github(auth=auth)
            changed = False
            for p in projects:
                # 1. Use language data stored in DB if available
                if p.languages:
                    for lang, byte_count in p.languages.items():
                        if isinstance(byte_count, int):
                            lang_stats[lang] = lang_stats.get(lang, 0) + byte_count
                    continue

                # 2. If not in DB, fetch from GitHub API and cache it
                repo_path = p.repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
                try:
                    repo = g.get_repo(repo_path)
                    langs = repo.get_languages()
                    p.languages = langs # Cache in DB
                    changed = True
                    
                    for lang, byte_count in langs.items():
                        if isinstance(byte_count, int):
                            lang_stats[lang] = lang_stats.get(lang, 0) + byte_count
                except Exception as repo_err:
                    print(f"Failed to fetch languages for {repo_path}: {repo_err}")
            
            if changed:
                db.commit() # Commit all at once
        except Exception as e:
            print(f"Failed to fetch languages from GitHub API: {e}")
            
    # Fall back to existing Insight data if GitHub API language fetch failed (fastest)
    if not lang_stats:
        from database.models import ProjectInsight
        insights = db.query(ProjectInsight).join(Project).filter(Project.user_id == user.id).all()
        for ins in insights:
            if ins.tech_stack and "language_distribution" in ins.tech_stack:
                for lang, count in ins.tech_stack["language_distribution"].items():
                    lang_stats[lang] = lang_stats.get(lang, 0) + count

    # Extract only the top 6 languages
    sorted_skills = sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)[:6]
    skills = {k: v for k, v in sorted_skills if v > 0}

    # Generated assets
    readmes = db.query(GeneratedReadme).join(Project).filter(Project.user_id == user.id).order_by(GeneratedReadme.created_at.desc()).limit(10).all()
    
    return {
        "user": {
            "name": user.name,
            "avatar_url": user.avatar_url,
            "github_username": user.github_username,
            "country": user.country,
            "job": user.job,
            "created_at": user.created_at
        },
        "skills": skills,
        "projects": [
            {
                "id": p.id,
                "repo_url": p.repo_url,
                "file_count": p.file_count,
                "created_at": p.created_at,
                "status": p.status,
                "has_readme": len(p.readmes) > 0 if p.readmes else False,
                "has_diagram": p.mermaid_code is not None,
                "latest_session_id": (
                    db.query(ChatSession.id)
                    .filter(ChatSession.project_id == p.id)
                    .order_by(ChatSession.created_at.desc())
                    .limit(1)
                    .scalar()
                )
            } for p in projects
        ],
        "assets": {
            "readmes": [
                {
                    "id": r.id, 
                    "project_id": r.project_id, 
                    "repo_url": r.project.repo_url, 
                    "created_at": r.created_at, 
                    "latest_session_id": (
                        db.query(ChatSession.id)
                        .filter(ChatSession.project_id == r.project_id)
                        .order_by(ChatSession.created_at.desc())
                        .limit(1)
                        .scalar()
                    )
                } for r in readmes
            ],
            "diagrams": [
                {
                    "id": p.id, 
                    "repo_url": p.repo_url, 
                    "created_at": p.created_at, 
                    "latest_session_id": (
                        db.query(ChatSession.id)
                        .filter(ChatSession.project_id == p.id)
                        .order_by(ChatSession.created_at.desc())
                        .limit(1)
                        .scalar()
                    )
                } for p in projects if p.mermaid_code
            ]
        }
    }

# Retrieve list of GitHub repositories
@router.get("/github/repos")
async def get_github_repos(current_user: User = Depends(get_current_user)):
    # Fall back to GITHUB_TOKEN env var if no user token available
    token = current_user.github_token or os.getenv("GITHUB_TOKEN")
    if not token:
        # Return empty list instead of error if no token at all
        return []

    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)

        # Get up to 20 of the user's own repositories sorted by most recently updated
        repos = g.get_user().get_repos(sort="updated", direction="desc")
        
        return [
            {
                "name": r.name,
                "full_name": r.full_name,
                "html_url": r.html_url,
                "description": r.description,
                "language": r.language,
                "stargazers_count": r.stargazers_count,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None
            } for r in repos[:20]
        ]
    except Exception as e:
        print(f"GitHub API Error: {e}")
        return []

# Router - GitHub
@router.get("/github/login")
async def github_login():
    with github_sso:
        return await github_sso.get_login_redirect()

@router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    # 1. Obtain access_token directly from GitHub
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Code not found")
    
    import httpx
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": "http://localhost:8000/auth/github/callback"
            },
            headers={"Accept": "application/json"}
        )
        token_data = token_response.json()
        github_token = token_data.get("access_token")
        
    if not github_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")

    # 2. Fetch user information (using PyGithub)
    # PyGithub is a synchronous library; run_in_threadpool could be used if needed,
    # but a simple direct call is used here for simplicity.
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    gh_user = g.get_user()

    # Structure data similarly to the SSOUser interface (to avoid ImportError)
    class GithubUser:
        def __init__(self, id, email, display_name, picture):
            self.id = id
            self.email = email
            self.display_name = display_name
            self.picture = picture
            self.provider = "github"
    
    sso_user = GithubUser(
        id=str(gh_user.id),
        email=gh_user.email or f"{gh_user.login}@github.com",
        display_name=gh_user.name or gh_user.login,
        picture=gh_user.avatar_url
    )
    
    github_username = gh_user.login
        
    return await process_sso_login(sso_user, "github", db, github_username=github_username, github_token=github_token)

    return await process_sso_login(sso_user, "github", db, github_username=github_username, github_token=github_token)


