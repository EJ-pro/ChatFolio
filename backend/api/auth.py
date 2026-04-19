import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO
from github import Github, Auth
from sqlalchemy import func

from database.database import get_db
from database.models import User, Project, GeneratedReadme, ProjectFile, ChatSession

router = APIRouter(prefix="/auth", tags=["auth"])

# 환경 변수에서 OAuth 정보 가져오기
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_if_not_set")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

# SSO 객체 초기화 (Redirect URI는 프론트엔드가 아니라 백엔드의 callback 주소입니다)
github_sso = GithubSSO(
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    redirect_uri="http://localhost:8000/auth/github/callback",
    allow_insecure_http=True # 개발 환경(http) 허용
)

google_sso = GoogleSSO(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri="http://localhost:8000/auth/google/callback",
    allow_insecure_http=True
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
                "has_readme": p.readme is not None,
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
    with github_sso:
        # verify_and_process는 내부적으로 access_token을 사용하여 유저 정보를 가져옴
        # 하지만 access_token 자체는 반환하지 않으므로, 커스텀 로직이 필요할 수 있음
        # fastapi-sso 버전에 따라 다르지만, sso_user.extra_data 등에 있을 수 있음
        sso_user = await github_sso.verify_and_process(request)
        
        # 깃허브 아이디(username) 추출
        # SSOUser 객체의 display_name을 기본으로 하되, 없을 경우 이메일 앞부분 사용
        github_username = sso_user.display_name or sso_user.email.split('@')[0]
        
    return await process_sso_login(sso_user, "github", db, github_username=github_username)

# 라우터 - Google
@router.get("/google/login")
async def google_login():
    with google_sso:
        return await google_sso.get_login_redirect()

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    with google_sso:
        sso_user = await google_sso.verify_and_process(request)
    return await process_sso_login(sso_user, "google", db)
