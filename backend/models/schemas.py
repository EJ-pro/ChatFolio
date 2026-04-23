from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# 저장소 분석 요청
class AnalyzeRequest(BaseModel):
    repo_url: str
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None
    force_update: Optional[bool] = False
    language: Optional[str] = "English"

# 채팅 메시지 요청
class ChatRequest(BaseModel):
    session_id: str
    query: str
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None
    language: Optional[str] = "English"

# 분석 상태 및 결과 응답
class AnalysisResponse(BaseModel):
    status: str
    session_id: str
    file_count: int
    node_count: int
    edge_count: int
    message: str

# 아키텍처 다이어그램 요청 및 응답
class DiagramRequest(BaseModel):
    session_id: str
    force_regenerate: Optional[bool] = False

class DiagramResponse(BaseModel):
    mermaid_code: str

# README 자동 생성 요청 및 응답
class ReadmeRequest(BaseModel):
    session_id: str
    force_regenerate: Optional[bool] = False
    user_inputs: Optional[Dict[str, str]] = None
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None
    languages: Optional[List[str]] = ["English"]

class ReadmeResponse(BaseModel):
    readme_content: str

# 새 채팅 세션 생성 요청
class NewSessionRequest(BaseModel):
    project_id: int
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    country: Optional[str] = None
    job: Optional[str] = None