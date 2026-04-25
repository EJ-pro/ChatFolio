from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.schemas import AnalyzeRequest, ChatRequest, AnalysisResponse, DiagramRequest, DiagramResponse, ReadmeRequest, ReadmeResponse, NewSessionRequest, ProfileUpdateRequest
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
from core.parser.factory import get_parser_result
from core.graph.graph_builder import DependencyGraphBuilder
from core.rag.engine import ChatFolioEngine
from database.models import init_db, Project, ProjectFile, ChatSession, ChatMessage, User, Inquiry, ProjectInsight, TokenUsage, GeneratedReadme
from database.database import get_db, SessionLocal
from api.auth import router as auth_router, get_current_user

load_dotenv()
init_db()

def record_token_usage(db: Session, user_id: int, model_name: str, feature_name: str, token_count: int):
    """토큰 사용량을 상세히 기록합니다."""
    if not token_count or token_count <= 0:
        return
    try:
        new_usage = TokenUsage(
            user_id=user_id,
            model_name=model_name,
            feature_name=feature_name,
            token_count=int(token_count)
        )
        db.add(new_usage)
        db.commit()
    except Exception as e:
        print(f"Failed to record token usage: {e}")
        db.rollback()

app = FastAPI(title="ChatFolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# 문의하기 등록 엔드포인트
from fastapi import Request
@app.post("/inquiries")
async def create_inquiry(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = await request.json()
    title = data.get("title")
    content = data.get("content")
    
    if not title or not content:
        raise HTTPException(status_code=400, detail="제목과 내용을 입력해주세요.")
        
    inquiry = Inquiry(
        user_id=current_user.id,
        title=title,
        content=content
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return {"status": "success", "message": "Your inquiry has been received."}

@app.patch("/user/profile")
async def update_user_profile(request: ProfileUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if request.country is not None:
        current_user.country = request.country
    if request.job is not None:
        current_user.job = request.job
    db.commit()
    db.refresh(current_user)
    return {"status": "success", "user": {"country": current_user.country, "job": current_user.job}}

@app.get("/stats/global")
async def get_global_stats(db: Session = Depends(get_db)):
    total_projects = db.query(Project).count()
    total_users = db.query(User).count()
    total_lines = db.query(func.sum(ProjectFile.line_count)).scalar() or 0
    total_nodes = db.query(func.sum(Project.node_count)).scalar() or 0
    return {
        "total_projects": total_projects,
        "total_users": total_users,
        "total_lines": total_lines,
        "total_nodes": total_nodes,
        "ai_health": 99.9
    }

engine_cache = {}

@app.post("/analyze")
async def analyze_repository(request: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if request.provider == "openai" and current_user.tier != "pro":
        raise HTTPException(status_code=402, detail="OpenAI 모델은 Pro 등급 전용입니다.")

    existing_project = db.query(Project).filter(Project.repo_url == request.repo_url, Project.user_id == current_user.id).first()
    if existing_project and not request.force_update:
        token = current_user.github_token or os.getenv("GITHUB_TOKEN")
        fetcher = GitHubFetcher(token=token)
        try:
            latest_commit = fetcher.fetch_latest_commit(request.repo_url)
            if latest_commit["hash"] == existing_project.last_commit_hash:
                existing_session = db.query(ChatSession).filter(ChatSession.project_id == existing_project.id, ChatSession.user_id == current_user.id, ChatSession.provider == request.provider, ChatSession.model_name == request.model_name).order_by(ChatSession.created_at.desc()).first()
                if existing_session:
                    if existing_session.id not in engine_cache:
                        all_project_files = {f.file_path: f.content for f in existing_project.files}
                        graph = nx.node_link_graph(existing_project.graph_data)
                        engine = ChatFolioEngine(all_project_files, graph, project_id=existing_project.id, provider=existing_session.provider, model_name=existing_session.model_name)
                        engine_cache[existing_session.id] = engine
                    async def quick_return():
                        result = {"status": "success", "session_id": existing_session.id, "file_count": existing_project.file_count, "node_count": existing_project.node_count, "edge_count": existing_project.edge_count, "message": "Loaded existing analysis result."}
                        yield f"data: RESULT:{json.dumps(result)}\n\n"
                    return StreamingResponse(quick_return(), media_type="text/event-stream")
        except: pass

    def generate():
        q = Queue()
        def progress_callback(msg): q.put(msg)
        def run_analysis():
            db_session = SessionLocal()
            try:
                token = current_user.github_token or os.getenv("GITHUB_TOKEN")
                fetcher = GitHubFetcher(token=token)
                commit_info, file_generator = fetcher.fetch_repo_files(request.repo_url, progress_callback=progress_callback)
                project = db_session.query(Project).filter(Project.repo_url == request.repo_url, Project.user_id == current_user.id).first()
                if project:
                    project.file_count = commit_info["total_files"]
                    project.last_commit_hash = commit_info["hash"]
                    project.last_commit_message = commit_info["message"]
                    db_session.query(ProjectFile).filter(ProjectFile.project_id == project.id).delete()
                else:
                    project = Project(user_id=current_user.id, repo_url=request.repo_url, file_count=commit_info["total_files"], last_commit_hash=commit_info["hash"], last_commit_message=commit_info["message"])
                    db_session.add(project)
                db_session.flush()
                all_files, all_meta = {}, {}
                lang_counts, detected_frameworks, used_parsers = {}, set(), set()
                for path, content in file_generator:
                    all_files[path] = content
                    meta = get_parser_result(path, content)
                    parsed_data = meta.get("metadata_json", {}).get("parsed", {})
                    if "language" in parsed_data:
                        lang = parsed_data["language"]
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                    for key, val in parsed_data.items():
                        if key.startswith("is_") and val is True:
                            detected_frameworks.add(key.replace("is_", "").replace("_", " ").title())
                    if path.endswith(('.kt', '.kts', '.java', '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs')):
                        all_meta[path] = meta
                    db_session.add(ProjectFile(project_id=project.id, file_path=path, content=content, line_count=meta.get("line_count", 0), file_size=len(content.encode('utf-8')), keywords=meta.get("keywords", []), metadata_json=meta.get("metadata_json", {})))
                
                tech_stack_json = {"main_language": max(lang_counts, key=lang_counts.get) if lang_counts else "Unknown", "language_distribution": lang_counts, "frameworks": list(detected_frameworks)}
                db_session.query(ProjectInsight).filter(ProjectInsight.project_id == project.id).delete()
                db_session.add(ProjectInsight(project_id=project.id, tech_stack=tech_stack_json, summary=f"Analyzed {project.repo_url}"))
                
                builder = DependencyGraphBuilder()
                graph = builder.build_graph(all_meta)
                project.node_count, project.edge_count, project.graph_data = graph.number_of_nodes(), graph.number_of_edges(), nx.node_link_data(graph)
                
                chat_session = ChatSession(user_id=current_user.id, project_id=project.id, provider=request.provider, model_name=request.model_name)
                db_session.add(chat_session)
                project.status = "COMPLETED"
                db_session.commit()
                db_session.refresh(chat_session)
                
                engine = ChatFolioEngine(all_files, graph, project_id=project.id, tech_stack=tech_stack_json, provider=request.provider, model_name=request.model_name)
                engine_cache[chat_session.id] = engine
                
                q.put(f"RESULT:{json.dumps({'status': 'success', 'session_id': chat_session.id, 'file_count': project.file_count, 'message': 'Analysis complete'})}")
                q.put(None)
            except Exception as e:
                db_session.rollback()
                q.put(f"ERROR:{str(e)}")
                q.put(None)
            finally: db_session.close()
        Thread(target=run_analysis).start()
        while True:
            msg = q.get()
            if msg is None: break
            yield f"data: {msg}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/chat")
async def chat_ask(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session: raise HTTPException(status_code=404, detail="Session not found")
    project = chat_session.project
    engine = engine_cache.get(session_id)
    if not engine:
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        engine = ChatFolioEngine(all_project_files, graph, project_id=project.id, provider=chat_session.provider, model_name=chat_session.model_name)
        engine_cache[session_id] = engine
    try:
        db.add(ChatMessage(session_id=session_id, role="user", content=request.query))
        result = engine.ask(request.query, language=request.language)
        db.add(ChatMessage(session_id=session_id, role="assistant", content=result["answer"], sources=result["sources"], evaluation=result.get("evaluation")))
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return [{"id": m.id, "role": m.role, "content": m.content, "sources": m.sources, "evaluation": m.evaluation, "created_at": m.created_at} for m in messages]

@app.get("/projects")
async def get_user_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()
    return [{
        "id": p.id, "repo_url": p.repo_url, "file_count": p.file_count, "last_commit_message": p.last_commit_message,
        "latest_session_id": db.query(ChatSession).filter(ChatSession.project_id == p.id).order_by(ChatSession.created_at.desc()).first().id if db.query(ChatSession).filter(ChatSession.project_id == p.id).count() > 0 else None
    } for p in projects]

@app.post("/generate/network")
async def generate_network_data(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    graph = nx.node_link_graph(chat_session.project.graph_data)
    nodes, links = [], []
    degree_dict = dict(graph.degree())
    for node in graph.nodes():
        nodes.append({"id": node, "name": node.split('/')[-1], "group": node.split('/')[-2] if '/' in node else "root", "val": max(1, min(20, degree_dict.get(node, 1)))})
    for u, v in graph.edges():
        links.append({"source": u, "target": v})
    return {"nodes": nodes, "links": links}

@app.post("/generate/architecture-analysis")
async def generate_architecture_analysis(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    engine = engine_cache.get(request.session_id)
    if not engine:
        project = chat_session.project
        engine = ChatFolioEngine({f.file_path: f.content for f in project.files}, nx.node_link_graph(project.graph_data), project_id=project.id, provider=chat_session.provider, model_name=chat_session.model_name)
        engine_cache[request.session_id] = engine
    return {"analysis": engine.analyze_architecture(language="Korean" if current_user.country == "South Korea" else "English").get("analysis")}

@app.post("/generate/pipeline")
async def generate_project_pipeline(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    engine = engine_cache.get(request.session_id)
    if not engine:
        project = chat_session.project
        engine = ChatFolioEngine({f.file_path: f.content for f in project.files}, nx.node_link_graph(project.graph_data), project_id=project.id, provider=chat_session.provider, model_name=chat_session.model_name)
        engine_cache[request.session_id] = engine
    return engine.generate_pipeline(language="Korean" if current_user.country == "South Korea" else "English")

@app.get("/readmes/{project_id}")
async def get_project_readmes(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    readmes = db.query(GeneratedReadme).filter(GeneratedReadme.project_id == project_id).order_by(GeneratedReadme.created_at.desc()).all()
    return [{"id": r.id, "content": r.content, "template_type": r.template_type, "created_at": r.created_at} for r in readmes]

@app.post("/generate/readme")
async def generate_readme(request: ReadmeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    engine = engine_cache.get(request.session_id)
    result = engine.generate_readme(languages=request.languages)
    new_readme = GeneratedReadme(project_id=chat_session.project_id, content=result["readme_content"])
    db.add(new_readme)
    db.commit()
    return {"readme_content": result["readme_content"]}
