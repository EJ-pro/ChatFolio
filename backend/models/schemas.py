from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# 저장소 분석 요청
class AnalyzeRequest(BaseModel):
    repo_url: str

# 채팅 메시지 요청
class ChatRequest(BaseModel):
    query: str

# 분석 상태 및 결과 응답
class AnalysisResponse(BaseModel):
    status: str
    file_count: int
    node_count: int
    edge_count: int
    message: str