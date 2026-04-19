import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO

from database.database import get_db
from database.models import User

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
async def process_sso_login(sso_user, provider: str, db: Session):
    # 이메일로 기존 사용자 찾기
    user = db.query(User).filter(User.email == sso_user.email).first()
    
    if not user:
        # 없으면 새로 생성
        user = User(
            provider=provider,
            email=sso_user.email,
            name=sso_user.display_name or sso_user.email.split('@')[0],
            avatar_url=sso_user.picture
        )
        db.add(user)
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
        "avatar_url": current_user.avatar_url,
        "provider": current_user.provider
    }

# 라우터 - GitHub
@router.get("/github/login")
async def github_login():
    with github_sso:
        return await github_sso.get_login_redirect()

@router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    with github_sso:
        sso_user = await github_sso.verify_and_process(request)
    return await process_sso_login(sso_user, "github", db)

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
