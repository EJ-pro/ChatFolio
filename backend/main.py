from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from models.schemas import AnalyzeRequest, ChatRequest, AnalysisResponse, DiagramRequest, DiagramResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import networkx as nx
from dotenv import load_dotenv

from core.parser.github_fetcher import GitHubFetcher
from core.parser.kotlin_parser import parse_kotlin_code
from core.graph.graph_builder import DependencyGraphBuilder
from core.rag.engine import ChatFolioEngine
from database.models import init_db, Project, ProjectFile, ChatSession, ChatMessage, User
from database.database import get_db

# 라우터 및 의존성 추가
from api.auth import router as auth_router, get_current_user

load_dotenv()

init_db()

app = FastAPI(title="ChatFolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

engine_cache = {}

@app.post("/analyze")
async def analyze_repository(request: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token = os.getenv("GITHUB_TOKEN")
    try:
        fetcher = GitHubFetcher(token=token)
        all_files = fetcher.fetch_repo_files(request.repo_url)
        
        # 1. 그래프용 필터 (현재는 Kotlin 중심)
        kt_files_for_graph = {p: c for p, c in all_files.items() if p.endswith(('.kt', '.kts'))}
        
        # 2. 전체 수집용 필터 (RAG 컨텍스트용)
        # 소스코드, 설정파일, 문서 등 포함
        relevant_extensions = (
            '.kt', '.kts', '.java', '.py', '.js', '.ts', '.tsx', '.jsx', 
            '.cpp', '.h', '.c', '.go', '.rs', '.swift', '.svelte', '.html', '.css',
            '.json', '.yaml', '.yml', '.toml', '.xml', '.properties', '.gradle',
            '.md', '.txt', '.sh', '.dockerfile', 'dockerfile'
        )
        relevant_files = {p: c for p, c in all_files.items() if p.lower().endswith(relevant_extensions) or p.lower() == 'dockerfile'}
        
        all_meta = {p: parse_kotlin_code(c) for p, c in kt_files_for_graph.items()}
        builder = DependencyGraphBuilder()
        graph = builder.build_graph(all_meta)
        
        graph_data = nx.node_link_data(graph)
        
        project = Project(
            user_id=current_user.id,
            repo_url=request.repo_url,
            file_count=len(relevant_files),
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
            graph_data=graph_data
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        project_files = [
            ProjectFile(project_id=project.id, file_path=p, content=c)
            for p, c in relevant_files.items()
        ]
        db.add_all(project_files)
        
        chat_session = ChatSession(
            user_id=current_user.id,
            project_id=project.id,
            provider=request.provider,
            model_name=request.model_name
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
        engine = ChatFolioEngine(relevant_files, graph, provider=request.provider, model_name=request.model_name)
        engine_cache[chat_session.id] = engine
        
        return {
            "status": "success",
            "session_id": chat_session.id,
            "file_count": project.file_count,
            "node_count": project.node_count,
            "edge_count": project.edge_count,
            "message": "분석이 완료되었습니다."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_code(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
    # 권한 검사
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 세션에 접근할 권한이 없습니다.")
        
    engine = engine_cache.get(session_id)
    
    if not engine:
        project = chat_session.project
        if not project or not project.graph_data:
            raise HTTPException(status_code=404, detail="프로젝트 그래프 정보를 찾을 수 없습니다.")
            
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        
        # 세션에 저장된 모델 정보 사용
        engine = ChatFolioEngine(
            all_project_files, 
            graph, 
            provider=chat_session.provider, 
            model_name=chat_session.model_name
        )
        engine_cache[session_id] = engine

    try:
        user_msg = ChatMessage(session_id=session_id, role="user", content=request.query)
        db.add(user_msg)
        
        result = engine.ask(request.query)
        
        ai_msg = ChatMessage(
            session_id=session_id, 
            role="assistant", 
            content=result["answer"],
            sources=result["sources"]
        )
        db.add(ai_msg)
        db.commit()
        
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/diagram", response_model=DiagramResponse)
async def generate_architecture_diagram(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
    engine = engine_cache.get(session_id)
    if not engine:
        project = chat_session.project
        if not project or not project.graph_data:
            raise HTTPException(status_code=404, detail="프로젝트 그래프 정보를 찾을 수 없습니다.")
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        
        engine = ChatFolioEngine(
            all_project_files, 
            graph, 
            provider=chat_session.provider, 
            model_name=chat_session.model_name
        )
        engine_cache[session_id] = engine
        
    try:
        mermaid_code = engine.generate_mermaid()
        return DiagramResponse(mermaid_code=mermaid_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))