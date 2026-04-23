from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Repository analysis request
class AnalyzeRequest(BaseModel):
    repo_url: str
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None
    force_update: Optional[bool] = False
    language: Optional[str] = "English"

# Chat message request
class ChatRequest(BaseModel):
    session_id: str
    query: str
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None
    language: Optional[str] = "English"

# Analysis status and result response
class AnalysisResponse(BaseModel):
    status: str
    session_id: str
    file_count: int
    node_count: int
    edge_count: int
    message: str

# Architecture diagram request and response
class DiagramRequest(BaseModel):
    session_id: str
    force_regenerate: Optional[bool] = False

class DiagramResponse(BaseModel):
    mermaid_code: str

# README auto-generation request and response
class ReadmeRequest(BaseModel):
    session_id: str
    force_regenerate: Optional[bool] = False
    user_inputs: Optional[Dict[str, str]] = None
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None
    languages: Optional[List[str]] = ["English"]

class ReadmeResponse(BaseModel):
    readme_content: str

# New chat session creation request
class NewSessionRequest(BaseModel):
    project_id: int
    provider: Optional[str] = "groq"
    model_name: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    country: Optional[str] = None
    job: Optional[str] = None