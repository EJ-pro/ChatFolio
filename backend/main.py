from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from models.schemas import AnalyzeRequest, ChatRequest, AnalysisResponse, DiagramRequest, DiagramResponse, ReadmeRequest, ReadmeResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import os
import networkx as nx
from dotenv import load_dotenv
import json
import asyncio
from queue import Queue
from threading import Thread

from core.parser.github_fetcher import GitHubFetcher
from core.parser.kotlin_parser import parse_kotlin_code
from core.graph.graph_builder import DependencyGraphBuilder
from core.rag.engine import ChatFolioEngine
from database.models import init_db, Project, ProjectFile, ChatSession, ChatMessage, User
from database.database import get_db
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
    # 1. 이미 분석된 프로젝트가 있는지 확인
    existing_project = db.query(Project).filter(
        Project.repo_url == request.repo_url,
        Project.user_id == current_user.id
    ).first()
    
    if existing_project:
        existing_session = db.query(ChatSession).filter(
            ChatSession.project_id == existing_project.id,
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.created_at.desc()).first()
        
        if existing_session:
            # 엔진 캐시 확인 및 복구
            if existing_session.id not in engine_cache:
                all_project_files = {f.file_path: f.content for f in existing_project.files}
                graph = nx.node_link_graph(existing_project.graph_data)
                engine = ChatFolioEngine(
                    all_project_files, 
                    graph, 
                    provider=existing_session.provider, 
                    model_name=existing_session.model_name
                )
                engine_cache[existing_session.id] = engine
                
            async def quick_return():
                result = {
                    "status": "success",
                    "session_id": existing_session.id,
                    "file_count": existing_project.file_count,
                    "node_count": existing_project.node_count,
                    "edge_count": existing_project.edge_count,
                    "message": "기존 분석 결과를 불러왔습니다."
                }
                yield f"data: RESULT:{json.dumps(result)}\n\n"
            
            return StreamingResponse(quick_return(), media_type="text/event-stream")

    def generate():
        q = Queue()
        
        def progress_callback(msg):
            q.put(msg)
            
        def run_analysis():
            try:
                token = os.getenv("GITHUB_TOKEN")
                fetcher = GitHubFetcher(token=token)
                all_files = fetcher.fetch_repo_files(request.repo_url, progress_callback=progress_callback)
                
                # 1. 그래프용 필터
                kt_files_for_graph = {p: c for p, c in all_files.items() if p.endswith(('.kt', '.kts'))}
                
                q.put("📊 의존성 그래프 분석 중...")
                all_meta = {p: parse_kotlin_code(c) for p, c in kt_files_for_graph.items()}
                builder = DependencyGraphBuilder()
                graph = builder.build_graph(all_meta)
                graph_data = nx.node_link_data(graph)
                
                q.put("💾 데이터베이스 저장 중...")
                project = Project(
                    user_id=current_user.id,
                    repo_url=request.repo_url,
                    file_count=len(all_files), 
                    node_count=graph.number_of_nodes(),
                    edge_count=graph.number_of_edges(),
                    graph_data=graph_data
                )
                db.add(project)
                db.commit()
                db.refresh(project)
                
                project_files = [
                    ProjectFile(project_id=project.id, file_path=p, content=c)
                    for p, c in all_files.items()
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
                
                engine = ChatFolioEngine(all_files, graph, provider=request.provider, model_name=request.model_name)
                engine_cache[chat_session.id] = engine
                
                result = {
                    "status": "success",
                    "session_id": chat_session.id,
                    "file_count": project.file_count,
                    "node_count": project.node_count,
                    "edge_count": project.edge_count,
                    "message": "분석이 완료되었습니다."
                }
                q.put(f"RESULT:{json.dumps(result)}")
                q.put(None)
            except Exception as e:
                q.put(f"ERROR:{str(e)}")
                q.put(None)

        Thread(target=run_analysis).start()
        
        while True:
            msg = q.get()
            if msg is None:
                break
            yield f"data: {msg}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/chat")
async def chat_with_code(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 세션에 접근할 권한이 없습니다.")
        
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
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="프로젝트 그래프 정보를 찾을 수 없습니다.")

    # 1. DB에 캐시된 다이어그램이 있고, 강제 재생성 요청이 아니라면 즉시 반환
    if project.mermaid_code and not request.force_regenerate:
        return DiagramResponse(mermaid_code=project.mermaid_code)

    # 2. 캐시가 없거나 강제 재생성 요청이면 LLM을 통해 생성
    engine = engine_cache.get(session_id)
    if not engine:
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
        
        # 생성된 코드를 DB에 캐싱
        project.mermaid_code = mermaid_code
        db.commit()
        
        return DiagramResponse(mermaid_code=mermaid_code)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects")
async def get_user_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()
    
    result = []
    for p in projects:
        # 각 프로젝트의 최신 세션 가져오기
        latest_session = db.query(ChatSession).filter(ChatSession.project_id == p.id).order_by(ChatSession.created_at.desc()).first()
        result.append({
            "id": p.id,
            "repo_url": p.repo_url,
            "file_count": p.file_count,
            "created_at": p.created_at,
            "latest_session_id": latest_session.id if latest_session else None
        })
        
    return result

@app.post("/generate/network")
async def generate_network_data(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="프로젝트 그래프 정보를 찾을 수 없습니다.")
        
    graph = nx.node_link_graph(project.graph_data)
    
    nodes = []
    links = []
    
    degree_dict = dict(graph.degree())
    
    for node in graph.nodes():
        parts = node.split('/')
        name = parts[-1]
        group = parts[-2] if len(parts) > 1 else "root"
        
        # 노드의 연결 수(degree)를 계산하여 크기(val) 결정 (최소 1, 최대 20으로 제한)
        val = max(1, min(20, degree_dict.get(node, 1)))
        
        nodes.append({
            "id": node,
            "name": name,
            "group": group,
            "val": val
        })
        
    for u, v in graph.edges():
        links.append({
            "source": u,
            "target": v
        })
        
    return {"nodes": nodes, "links": links}

@app.post("/generate/readme", response_model=ReadmeResponse)
async def generate_readme(request: ReadmeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="프로젝트 그래프 정보를 찾을 수 없습니다.")
        
    engine = engine_cache.get(session_id)
    if not engine:
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
        readme_content = engine.generate_readme()
        return ReadmeResponse(readme_content=readme_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))