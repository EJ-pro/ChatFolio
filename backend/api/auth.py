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
from core.persona.analyzer import PersonaAnalyzer
from core.rag.engine import ChatFolioEngine

router = APIRouter(prefix="/auth", tags=["auth"])

# 환경 변수에서 OAuth 정보 가져오기
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_if_not_set")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

# SSO 객체 초기화 (Redirect URI는 프론트엔드가 아니라 백엔드의 callback 주소입니다)
github_sso = GithubSSO(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri="http://localhost:8000/auth/github/callback",
    allow_insecure_http=True, # 개발 환경(http) 허용
    scope=["user:email", "repo"] # 프라이빗 레포지토리 접근 권한 추가
)

# JWT 생성 유틸리티
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# 현재 로그인한 사용자 검증 (Dependency)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="토큰 검증에 실패했습니다.")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    return user

# 공통 소셜 로그인 콜백 처리 로직
async def process_sso_login(sso_user, provider: str, db: Session, github_username: str = None, github_token: str = None):
    # 이메일로 기존 사용자 찾기
    user = db.query(User).filter(User.email == sso_user.email).first()
    
    if not user:
        # 없으면 새로 생성
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
        # 정보 업데이트
        user.name = sso_user.display_name or user.name
        user.avatar_url = sso_user.picture or user.avatar_url
        if github_username:
            user.github_username = github_username
        if github_token:
            user.github_token = github_token
    
    db.commit()
    db.refresh(user)
    
    # JWT 발급
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # 프론트엔드로 리다이렉트 (토큰 포함)
    frontend_url = f"http://localhost/auth/callback?token={access_token}"
    return RedirectResponse(url=frontend_url)

# 현재 사용자 정보 조회
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "github_username": current_user.github_username,
        "avatar_url": current_user.avatar_url,
        "provider": current_user.provider
    }

# 유저 마이페이지 프로필 정보 조회
@router.get("/profile/{username}")
async def get_user_profile(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.github_username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    # 프로젝트 데이터 가져오기
    projects = db.query(Project).filter(Project.user_id == user.id).all()
    
    # 스킬 통계 (Python에서 처리하여 범용성 확보)
    # 간단하게 분석된 프로젝트의 파일 확장자 분포 계산
    all_files = db.query(ProjectFile.file_path).join(Project).filter(Project.user_id == user.id).all()
    
    ext_stats = {}
    for f in all_files:
        ext = f.file_path.split('.')[-1].lower() if '.' in f.file_path else 'others'
        ext_stats[ext] = ext_stats.get(ext, 0) + 1
    
    # 상위 5개 언어만 추출
    sorted_skills = sorted(ext_stats.items(), key=lambda x: x[1], reverse=True)[:6]
    skills = {k: v for k, v in sorted_skills if v > 5}

    # 생성된 자산
    readmes = db.query(GeneratedReadme).join(Project).filter(Project.user_id == user.id).order_by(GeneratedReadme.created_at.desc()).limit(10).all()
    
    return {
        "user": {
            "name": user.name,
            "avatar_url": user.avatar_url,
            "github_username": user.github_username,
            "created_at": user.created_at,
            "persona_data": user.persona_data
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

# 깃허브 레포지토리 목록 조회
@router.get("/github/repos")
async def get_github_repos(current_user: User = Depends(get_current_user)):
    # 토큰이 없으면 환경변수 GITHUB_TOKEN이라도 시도
    token = current_user.github_token or os.getenv("GITHUB_TOKEN")
    if not token:
        # 토큰이 아예 없으면 빈 리스트 반환 (에러 대신)
        return []
    
    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        
        # 본인의 레포지토리 최신순 20개
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

# 라우터 - GitHub
@router.get("/github/login")
async def github_login():
    with github_sso:
        return await github_sso.get_login_redirect()

@router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    # 1. 깃허브로부터 access_token 직접 획득
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

    # 2. 유저 정보 획득 (PyGithub 사용)
    # PyGithub은 동기 라이브러리이므로 필요시 run_in_threadpool 등을 고려할 수 있으나 
    # 여기서는 간단히 직접 호출
    auth = Auth.Token(github_token)
    g = Github(auth=auth)
    gh_user = g.get_user()
    
    # SSOUser 인터페이스와 유사하게 데이터 구조화 (ImportError 방지)
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

# 코더 페르소나 (MBTI) 분석 엔드포인트
@router.post("/persona/analyze")
async def analyze_user_persona(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.github_token:
        raise HTTPException(status_code=400, detail="GitHub 연동이 필요합니다.")
    
    # 1. 모든 프로젝트의 파일 데이터 수집
    projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    if not projects:
        raise HTTPException(status_code=400, detail="분석된 프로젝트가 없습니다. 먼저 레포지토리를 분석해주세요.")
    
    all_files_data = {}
    last_repo_url = projects[0].repo_url
    
    for p in projects:
        files = db.query(ProjectFile).filter(ProjectFile.project_id == p.id).all()
        for f in files:
            all_files_data[f.file_path] = f.content
            
    # 2. 커밋 통계 수집 (최신 프로젝트 기준)
    fetcher = GitHubFetcher(token=current_user.github_token)
    try:
        commit_hours = fetcher.fetch_commit_stats(last_repo_url)
    except Exception:
        commit_hours = [] # 실패 시 빈 리스트
        
    # 3. 페르소나 분석 및 생성
    # LLM 엔진 임시 생성 (페르소나 생성용)
    engine = ChatFolioEngine({}, None, provider="groq", model_name="llama-3.3-70b-versatile")
    analyzer = PersonaAnalyzer(engine)
    
    metrics = analyzer.analyze_metrics(all_files_data, commit_hours)
    persona_result = await analyzer.generate_persona(metrics)
    
    # 4. 결과 저장
    current_user.persona_data = {
        "metrics": metrics,
        "persona": persona_result,
        "updated_at": datetime.utcnow().isoformat()
    }
    db.commit()
    
    return current_user.persona_data
