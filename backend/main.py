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
from database.models import init_db, Project, ProjectFile, ChatSession, ChatMessage, User, Inquiry, ProjectInsight, TokenUsage
from database.database import get_db, SessionLocal
from api.auth import router as auth_router, get_current_user

load_dotenv()
init_db()

def record_token_usage(db: Session, user_id: int, model_name: str, feature_name: str, token_count: int):
    """Records token usage in detail (who, when, where, which model, how many tokens)."""
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

# Inquiry submission endpoint
from fastapi import Request
@app.post("/inquiries")
async def create_inquiry(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = await request.json()
    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        raise HTTPException(status_code=400, detail="Please enter a title and content.")
        
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
    """Update the user's country and occupation information."""
    if request.country is not None:
        current_user.country = request.country
    if request.job is not None:
        current_user.job = request.job
        
    db.commit()
    db.refresh(current_user)
    return {
        "status": "success", 
        "user": {
            "country": current_user.country, 
            "job": current_user.job
        }
    }

@app.get("/stats/global")
async def get_global_stats(db: Session = Depends(get_db)):
    """Returns platform-wide statistics (public data)."""
    total_projects = db.query(Project).count()
    total_users = db.query(User).count()

    # Total cumulative code line count
    total_lines = db.query(func.sum(ProjectFile.line_count)).scalar() or 0
    # Total cumulative dependency node count
    total_nodes = db.query(func.sum(Project.node_count)).scalar() or 0
    
    return {
        "total_projects": total_projects,
        "total_users": total_users,
        "total_lines": total_lines,
        "total_nodes": total_nodes,
        "ai_health": 99.9 # Mock or calculate based on success rate if needed
    }

engine_cache = {}

@app.post("/analyze")
async def analyze_repository(request: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Check if the project has already been analyzed
    existing_project = db.query(Project).filter(
        Project.repo_url == request.repo_url,
        Project.user_id == current_user.id
    ).first()
    
    if existing_project and not request.force_update:
        # Check latest commit from GitHub
        token = current_user.github_token or os.getenv("GITHUB_TOKEN")
        fetcher = GitHubFetcher(token=token)
        try:
            latest_commit = fetcher.fetch_latest_commit(request.repo_url)
            if latest_commit["hash"] == existing_project.last_commit_hash:
                # Return existing result if commit is unchanged
                existing_session = db.query(ChatSession).filter(
                    ChatSession.project_id == existing_project.id,
                    ChatSession.user_id == current_user.id,
                    ChatSession.provider == request.provider,
                    ChatSession.model_name == request.model_name
                ).order_by(ChatSession.created_at.desc()).first()

                if existing_session:
                    # Check and restore engine cache
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
                            "message": "Loaded existing analysis result. (Latest)"
                        }
                        yield f"data: RESULT:{json.dumps(result)}\n\n"
                    
                    return StreamingResponse(quick_return(), media_type="text/event-stream")
                else:
                    # Same project but model changed: create a new ChatSession and reuse existing data
                    new_session = ChatSession(
                        user_id=current_user.id,
                        project_id=existing_project.id,
                        provider=request.provider,
                        model_name=request.model_name
                    )
                    db.add(new_session)
                    db.commit()
                    db.refresh(new_session)

                    all_project_files = {f.file_path: f.content for f in existing_project.files}
                    graph = nx.node_link_graph(existing_project.graph_data)
                    engine = ChatFolioEngine(
                        all_project_files, 
                        graph, 
                        provider=request.provider, 
                        model_name=request.model_name
                    )
                    engine_cache[new_session.id] = engine

                    async def new_session_return():
                        result = {
                            "status": "success",
                            "session_id": new_session.id,
                            "file_count": existing_project.file_count,
                            "node_count": existing_project.node_count,
                            "edge_count": existing_project.edge_count,
                            "message": "Starting a new analysis session based on existing project data."
                        }
                        yield f"data: RESULT:{json.dumps(result)}\n\n"
                    
                    return StreamingResponse(new_session_return(), media_type="text/event-stream")
            else:
                # Commit differs — proceed to analysis logic below
                print(f"Update detected for {request.repo_url}. Re-analyzing...")
        except Exception as e:
            print(f"Error checking for updates: {e}")
            # On error, safely attempt to return existing result (or skip and proceed with analysis)
            pass

    def generate():
        q = Queue()
        
        def progress_callback(msg):
            q.put(msg)
            
        def run_analysis():
            db_session = SessionLocal() # Create a separate session for thread safety
            try:
                # Use the user's personal token (allows private repo access)
                token = current_user.github_token or os.getenv("GITHUB_TOKEN")
                fetcher = GitHubFetcher(token=token)

                # 1. Fetch metadata and generator
                commit_info, file_generator = fetcher.fetch_repo_files(request.repo_url, progress_callback=progress_callback)
                
                # 2. Prepare project record (ID needed)
                project = db_session.query(Project).filter(Project.repo_url == request.repo_url, Project.user_id == current_user.id).first()
                if project:
                    project.file_count = commit_info["total_files"]
                    project.last_commit_hash = commit_info["hash"]
                    project.last_commit_message = commit_info["message"]
                    db_session.query(ProjectFile).filter(ProjectFile.project_id == project.id).delete()
                else:
                    project = Project(
                        user_id=current_user.id,
                        repo_url=request.repo_url,
                        file_count=commit_info["total_files"], 
                        last_commit_hash=commit_info["hash"],
                        last_commit_message=commit_info["message"]
                    )
                    db_session.add(project)
                
                db_session.flush() # Assign ID

                # 3. Iterate generator to save files and extract metadata
                all_files = {}
                all_meta = {}

                # Data for insight aggregation
                lang_counts = {}
                detected_frameworks = set()
                used_parsers = set()
                
                for path, content in file_generator:
                    all_files[path] = content
                    
                    # Extract metadata via the unified parser factory
                    meta = get_parser_result(path, content)
                    
                    # Insight aggregation logic
                    parsed_data = meta.get("metadata_json", {}).get("parsed", {})
                    if "language" in parsed_data:
                        lang = parsed_data["language"]
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                        used_parsers.add(f"{lang.title()} Parser")
                    elif "type" in parsed_data:
                        config_type = parsed_data["type"]
                        used_parsers.add(f"{config_type.title()} Config Parser")
                        
                    # Detect frameworks/requirements (extract is_* boolean flags)
                    for key, val in parsed_data.items():
                        if key.startswith("is_") and val is True:
                            framework_name = key.replace("is_", "").replace("_", " ").title()
                            detected_frameworks.add(framework_name)
                    
                    # Collect data for graph analysis (major language files only)
                    if path.endswith(('.kt', '.kts', '.java', '.py', '.js', '.ts', '.jsx', '.tsx', '.cpp', '.c', '.h', '.cc', '.go', '.rs', '.swift', '.rb', '.php', '.cs', '.dart')):
                        all_meta[path] = meta
                    
                    line_count = meta.get("line_count", 0)
                    keywords = meta.get("keywords", [])
                    metadata_json = meta.get("metadata_json", {})

                    # Add to DB immediately (memory-efficient storage)
                    new_file = ProjectFile(
                        project_id=project.id, 
                        file_path=path, 
                        content=content,
                        line_count=line_count,
                        file_size=len(content.encode('utf-8')),
                        keywords=keywords,
                        metadata_json=metadata_json
                    )
                    db_session.add(new_file)
                
                # 3.1 Fetch GitHub language statistics (for profile page optimization)
                try:
                    repo_path = request.repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
                    repo = fetcher.g.get_repo(repo_path)
                    gh_langs = repo.get_languages()
                    print(f"📊 [GitHub Languages] {repo_path}: {gh_langs}")
                    project.languages = gh_langs
                except Exception as lang_err:
                    print(f"Failed to fetch repo languages: {lang_err}")
                
                # --- [Save Project Insight to DB] ---
                q.put("💡 Identifying project insights...")
                main_language = max(lang_counts, key=lang_counts.get) if lang_counts else "Unknown"
                
                insight_summary = f"Main Language: {main_language.title()}"
                if detected_frameworks:
                    insight_summary += f" | Detected Tech/Env: {', '.join(detected_frameworks)}"
                
                tech_stack_json = {
                    "main_language": main_language,
                    "language_distribution": lang_counts,
                    "frameworks": list(detected_frameworks),
                    "used_parsers": list(used_parsers)
                }

                # Overwrite existing insight
                db_session.query(ProjectInsight).filter(ProjectInsight.project_id == project.id).delete()
                
                insight = ProjectInsight(
                    project_id=project.id,
                    tech_stack=tech_stack_json,
                    summary=insight_summary
                )
                db_session.add(insight)
                
                # 4. Dependency graph analysis
                q.put("📊 Analyzing dependency graph...")
                builder = DependencyGraphBuilder()
                graph = builder.build_graph(all_meta)
                graph_data = nx.node_link_data(graph)
                
                # Update project graph information
                project.node_count = graph.number_of_nodes()
                project.edge_count = graph.number_of_edges()
                project.graph_data = graph_data
                
                q.put("💾 Saving data to database...")
                
                chat_session = ChatSession(
                    user_id=current_user.id,
                    project_id=project.id,
                    provider=request.provider,
                    model_name=request.model_name
                )
                db_session.add(chat_session)
                
                # Atomic transaction commit
                project.status = "COMPLETED"
                db_session.commit()
                db_session.refresh(project)
                db_session.refresh(chat_session)

                
                engine = ChatFolioEngine(all_files, graph, tech_stack=tech_stack_json, provider=request.provider, model_name=request.model_name)
                engine_cache[chat_session.id] = engine
                
                result = {
                    "status": "success",
                    "session_id": chat_session.id,
                    "file_count": project.file_count,
                    "node_count": project.node_count,
                    "edge_count": project.edge_count,
                    "message": "Analysis completed."
                }
                q.put(f"RESULT:{json.dumps(result)}")
                q.put(None)
            except Exception as e:
                db_session.rollback()
                q.put(f"ERROR:{str(e)}")
                q.put(None)
            finally:
                db_session.close()

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
        raise HTTPException(status_code=404, detail="Session not found.")

    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this session.")
        
    engine = engine_cache.get(session_id)
    
    if not engine:
        project = chat_session.project
        if not project or not project.graph_data:
            raise HTTPException(status_code=404, detail="Project graph data not found.")
            
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        tech_stack = project.insight.tech_stack if project.insight else None
        
        engine = ChatFolioEngine(
            all_project_files, 
            graph, 
            tech_stack=tech_stack,
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

@app.get("/chat/session/{session_id}/info")
async def get_chat_session_info(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    return {
        "session_id": chat_session.id,
        "project_id": chat_session.project_id,
        "provider": chat_session.provider,
        "model_name": chat_session.model_name,
        "created_at": chat_session.created_at
    }

@app.get("/chat/sessions/{project_id}")
async def get_project_chat_sessions(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    sessions = db.query(ChatSession).filter(
        ChatSession.project_id == project_id,
        ChatSession.is_deleted == 0
    ).order_by(ChatSession.created_at.desc()).all()
    
    return [
        {
            "session_id": s.id,
            "title": s.title,
            "provider": s.provider,
            "model_name": s.model_name,
            "created_at": s.created_at
        } for s in sessions
    ]

@app.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    # Soft delete
    chat_session.is_deleted = 1
    db.commit()
    
    return {"status": "success", "message": "Chat session deleted successfully."}

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "sources": msg.sources,
            "created_at": msg.created_at
        } for msg in messages
    ]

@app.post("/chat/session/new")
async def create_new_chat_session(request: NewSessionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    new_session = ChatSession(
        user_id=current_user.id,
        project_id=project.id,
        provider=request.provider,
        model_name=request.model_name
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    all_project_files = {f.file_path: f.content for f in project.files}
    graph = nx.node_link_graph(project.graph_data)
    tech_stack = project.insight.tech_stack if project.insight else None
    
    engine = ChatFolioEngine(
        all_project_files, 
        graph, 
        tech_stack=tech_stack,
        provider=request.provider, 
        model_name=request.model_name
    )
    engine_cache[new_session.id] = engine
    
    return {
        "status": "success",
        "session_id": new_session.id,
        "project_id": project.id,
        "message": "New chat session created."
    }

@app.post("/chat")
async def chat_ask(request: ChatRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    query = request.query
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    project = chat_session.project
    if not project:
        raise HTTPException(status_code=404, detail="Associated project not found.")

    # 1. Fetch or load engine
    engine = engine_cache.get(session_id)
    
    # Create a new engine if a model change is requested or no cached engine exists
    need_new_engine = False
    if engine:
        if request.provider and engine.provider != request.provider:
            need_new_engine = True
        if request.model_name and engine.model_name != request.model_name:
            need_new_engine = True
            
    if not engine or need_new_engine:
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        tech_stack = project.insight.tech_stack if project.insight else None
        
        engine = ChatFolioEngine(
            all_project_files, 
            graph, 
            tech_stack=tech_stack,
            provider=request.provider or chat_session.provider, 
            model_name=request.model_name or chat_session.model_name
        )
        engine_cache[session_id] = engine
    
    try:
        # 2. Save user question
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=query
        )
        db.add(user_message)
        
        # 3. Run RAG engine (with language)
        result = engine.ask(query, language=request.language)
        answer = result.get("answer", "Sorry, I couldn't generate an answer.")
        sources = result.get("sources", [])
        
        # 4. Save answer
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            sources=sources
        )
        db.add(assistant_message)

        # --- Record token usage ---
        usage = result.get("usage", {})
        record_token_usage(
            db=db,
            user_id=current_user.id,
            model_name=engine.model_name,
            feature_name="Chat",
            token_count=usage.get("total_tokens", 0)
        )

        # 5. Summarize title for the first message
        is_first_msg = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count() == 1 # Only the user_message just added should be present
        if is_first_msg:
            try:
                res = engine.summarize_title(query)
                chat_session.title = res.get("title", query[:20])
                
                # Record title summarization token usage
                usage = res.get("usage", {})
                model = usage.get("model_name") or ("llama-3.1-8b-instant" if engine.provider == "groq" else "gpt-4o-mini")
                record_token_usage(
                    db=db,
                    user_id=current_user.id,
                    model_name=model,
                    feature_name="Chat-Title",
                    token_count=usage.get("total_tokens", 0)
                )
            except Exception as e:
                print(f"Title summarization failed: {e}")

        db.commit()
        
        return {
            "answer": answer,
            "sources": sources,
            "graph_trace": result.get("graph_trace", [])
        }
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/diagram", response_model=DiagramResponse)
async def generate_architecture_diagram(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="Project graph data not found.")

    # 1. Return immediately if a cached diagram exists and no forced regeneration was requested
    if project.mermaid_code and not request.force_regenerate:
        return DiagramResponse(mermaid_code=project.mermaid_code)

    # 2. Generate via LLM if cache is missing or forced regeneration is requested
    engine = engine_cache.get(session_id)
    if not engine:
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        tech_stack = project.insight.tech_stack if project.insight else None
        
        engine = ChatFolioEngine(
            all_project_files, 
            graph, 
            tech_stack=tech_stack,
            provider=chat_session.provider, 
            model_name=chat_session.model_name
        )
        engine_cache[session_id] = engine
        
    try:
        mermaid_code = engine.generate_mermaid()
        
        # Cache generated code in DB
        project.mermaid_code = mermaid_code
        db.commit()
        
        return DiagramResponse(mermaid_code=mermaid_code)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/check-update")
async def check_project_update(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    token = current_user.github_token or os.getenv("GITHUB_TOKEN")
    fetcher = GitHubFetcher(token=token)
    
    try:
        latest_commit = fetcher.fetch_latest_commit(project.repo_url)
        is_updated = latest_commit["hash"] != project.last_commit_hash
        
        return {
            "is_updated": is_updated,
            "latest_commit": latest_commit,
            "current_commit_hash": project.last_commit_hash
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects")
async def get_user_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = db.query(Project).filter(Project.user_id == current_user.id).order_by(Project.created_at.desc()).all()
    
    result = []
    for p in projects:
        # Fetch latest session and insight for each project
        latest_session = db.query(ChatSession).filter(ChatSession.project_id == p.id).order_by(ChatSession.created_at.desc()).first()
        insight = p.insight
        tech_stack = insight.tech_stack if insight else None

        result.append({
            "id": p.id,
            "repo_url": p.repo_url,
            "file_count": p.file_count,
            "last_commit_hash": p.last_commit_hash,
            "last_commit_message": p.last_commit_message,
            "created_at": p.created_at,
            "latest_session_id": latest_session.id if latest_session else None,
            "tech_stack": tech_stack
        })
        
    return result

@app.post("/generate/network")
async def generate_network_data(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="Project graph data not found.")
        
    graph = nx.node_link_graph(project.graph_data)
    
    nodes = []
    links = []
    
    degree_dict = dict(graph.degree())
    
    for node in graph.nodes():
        parts = node.split('/')
        name = parts[-1]
        group = parts[-2] if len(parts) > 1 else "root"
        
        # Calculate node degree and determine size (val), clamped between 1 and 20
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
        raise HTTPException(status_code=404, detail="Session not found.")
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="Project graph data not found.")
        
    # 1. Check cache
    from database.models import GeneratedReadme
    latest_readme = db.query(GeneratedReadme).filter(GeneratedReadme.project_id == project.id).order_by(GeneratedReadme.created_at.desc()).first()
    
    if latest_readme and not request.force_regenerate:
        return ReadmeResponse(readme_content=latest_readme.content)
        
    engine = engine_cache.get(session_id)
    if not engine:
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        tech_stack = project.insight.tech_stack if project.insight else None
        
        engine = ChatFolioEngine(
            all_project_files, 
            graph, 
            tech_stack=tech_stack,
            provider=chat_session.provider, 
            model_name=chat_session.model_name
        )
        engine_cache[session_id] = engine
        
    try:
        # Override LLM if provided in request
        temp_llm = None
        if request.provider and request.model_name:
            if request.provider == "openai":
                from langchain_openai import ChatOpenAI
                temp_llm = ChatOpenAI(model=request.model_name, temperature=0)
            elif request.provider == "groq":
                from langchain_groq import ChatGroq
                temp_llm = ChatGroq(model=request.model_name, temperature=0)
        
        result = engine.generate_readme(
            request.user_inputs, 
            llm=temp_llm, 
            provider=request.provider, 
            model_name=request.model_name,
            languages=request.languages
        )
        readme_content = result.get("readme_content", "")
        usage_map = result.get("usage", {}) # { model_name: total_tokens }
        
        # Loop-record usage per model
        for model, tokens in usage_map.items():
            record_token_usage(
                db=db,
                user_id=current_user.id,
                model_name=model,
                feature_name="Readme",
                token_count=tokens
            )
        
        # Always create a new version
        new_readme = GeneratedReadme(project_id=project.id, content=readme_content)
        db.add(new_readme)
        db.commit()
        
        return ReadmeResponse(readme_content=readme_content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/readmes/{project_id}")
async def get_project_readmes(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    from database.models import GeneratedReadme
    readmes = db.query(GeneratedReadme).filter(GeneratedReadme.project_id == project.id).order_by(GeneratedReadme.created_at.desc()).all()
    
    return [
        {
            "id": r.id,
            "content": r.content,
            "template_type": r.template_type,
            "created_at": r.created_at
        } for r in readmes
    ]

@app.post("/generate/architecture-analysis")
async def generate_architecture_analysis(request: DiagramRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session_id = request.session_id
    
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="Project graph data not found.")
        
    engine = engine_cache.get(session_id)
    if not engine:
        import networkx as nx
        graph = nx.node_link_graph(project.graph_data)
        all_project_files = {f.file_path: f.content for f in project.files}
        tech_stack = project.insight.tech_stack if project.insight else None
        
        engine = ChatFolioEngine(
            all_project_files, 
            graph, 
            tech_stack=tech_stack,
            provider=chat_session.provider, 
            model_name=chat_session.model_name
        )
        engine_cache[session_id] = engine
        
    # Language setting (based on user country)
    language = "English"
    if current_user.country == "South Korea":
        language = "Korean"
        
    try:
        result = engine.analyze_architecture(language=language)
        analysis = result.get("analysis")
        usage = result.get("usage", {})
        
        record_token_usage(
            db=db,
            user_id=current_user.id,
            model_name=engine.model_name,
            feature_name="Architecture",
            token_count=usage.get("total_tokens", 0)
        )
        
        return {"analysis": analysis}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))