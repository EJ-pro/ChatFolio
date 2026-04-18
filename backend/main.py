from fastapi import FastAPI, HTTPException
# models 폴더 안의 schemas.py 파일에서 우리가 만든 클래스들을 가져옵니다.
from models.schemas import AnalyzeRequest, ChatRequest, AnalysisResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# 우리가 만든 모듈들
from core.parser.github_fetcher import GitHubFetcher
from core.parser.kotlin_parser import parse_kotlin_code
from core.graph.graph_builder import DependencyGraphBuilder
from core.rag.engine import ChatFolioEngine

load_dotenv()
app = FastAPI(title="ChatFolio API")

# CORS 설정 (프론트엔드 통신 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션별 엔진 관리를 위한 임시 저장소
# (실제 운영시에는 Redis나 인메모리 캐시 사용 권장)
project_session = {
    "engine": None,
    "files": None,
    "graph": None
}

@app.post("/analyze")
async def analyze_repository(request: AnalyzeRequest):
    token = os.getenv("GITHUB_TOKEN")
    try:
        # 1. 수집
        fetcher = GitHubFetcher(token=token)
        files = fetcher.fetch_repo_files(request.repo_url)
        kt_files = {p: c for p, c in files.items() if p.endswith(('.kt', '.kts'))}
        
        # 2. 분석 및 그래프 구축
        all_meta = {p: parse_kotlin_code(c) for p, c in kt_files.items()}
        builder = DependencyGraphBuilder()
        graph = builder.build_graph(all_meta)
        
        # 3. RAG 엔진 초기화
        engine = ChatFolioEngine(kt_files, graph)
        
        # 세션 저장
        project_session["engine"] = engine
        project_session["files"] = kt_files
        project_session["graph"] = graph
        
        return {
            "status": "success",
            "file_count": len(kt_files),
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "message": "분석이 완료되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_code(request: ChatRequest):
    if not project_session["engine"]:
        raise HTTPException(status_code=400, detail="먼저 프로젝트를 분석해야 합니다.")
    
    try:
        result = project_session["engine"].ask(request.query)
        return result # {answer, sources, graph_trace} 반환
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))