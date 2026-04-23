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
from database.models import init_db, Project, ProjectFile, ChatSession, ChatMessage, User, Inquiry, ProjectInsight
from database.database import get_db, SessionLocal
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
    """사용자 국가 및 직업 정보를 업데이트"""
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
    """플랫폼 전체 통계를 반환 (공개 데이터)"""
    total_projects = db.query(Project).count()
    total_users = db.query(User).count()
    
    # 누적 코드 라인 수 합계
    total_lines = db.query(func.sum(ProjectFile.line_count)).scalar() or 0
    # 누적 의존성 노드 수 합계
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
    # 1. 이미 분석된 프로젝트가 있는지 확인
    existing_project = db.query(Project).filter(
        Project.repo_url == request.repo_url,
        Project.user_id == current_user.id
    ).first()
    
    if existing_project and not request.force_update:
        # GitHub에서 최신 커밋 확인
        token = current_user.github_token or os.getenv("GITHUB_TOKEN")
        fetcher = GitHubFetcher(token=token)
        try:
            latest_commit = fetcher.fetch_latest_commit(request.repo_url)
            if latest_commit["hash"] == existing_project.last_commit_hash:
                # 커밋이 동일하면 기존 결과 반환
                existing_session = db.query(ChatSession).filter(
                    ChatSession.project_id == existing_project.id,
                    ChatSession.user_id == current_user.id,
                    ChatSession.provider == request.provider,
                    ChatSession.model_name == request.model_name
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
                            "message": "Loaded existing analysis result. (Latest)"
                        }
                        yield f"data: RESULT:{json.dumps(result)}\n\n"
                    
                    return StreamingResponse(quick_return(), media_type="text/event-stream")
                else:
                    # 동일 프로젝트지만 모델이 변경된 경우: 새 ChatSession 생성 및 기존 데이터 재사용
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
                # 커밋이 다름 -> 아래의 분석 로직으로 진행
                print(f"Update detected for {request.repo_url}. Re-analyzing...")
        except Exception as e:
            print(f"Error checking for updates: {e}")
            # 에러 발생 시 안전하게 기존 결과 반환 시도 (또는 무시하고 분석 진행)
            pass

    def generate():
        q = Queue()
        
        def progress_callback(msg):
            q.put(msg)
            
        def run_analysis():
            db_session = SessionLocal() # 스레드 안전성을 위해 별도의 세션 생성
            try:
                # 사용자의 개인 토큰 사용 (프라이빗 레포 접근 가능)
                token = current_user.github_token or os.getenv("GITHUB_TOKEN")
                fetcher = GitHubFetcher(token=token)
                
                # 1. 메타데이터와 제너레이터 가져오기
                commit_info, file_generator = fetcher.fetch_repo_files(request.repo_url, progress_callback=progress_callback)
                
                # 2. 프로젝트 레코드 준비 (ID가 필요함)
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
                
                db_session.flush() # ID 발급

                # 3. 제너레이터를 순회하며 파일 저장 및 메타데이터 추출
                all_files = {}
                all_meta = {}
                
                # 인사이트 집계용 데이터
                lang_counts = {}
                detected_frameworks = set()
                used_parsers = set()
                
                for path, content in file_generator:
                    all_files[path] = content
                    
                    # 통합 파서 팩토리를 통해 메타데이터 추출
                    meta = get_parser_result(path, content)
                    
                    # 인사이트 집계 로직
                    parsed_data = meta.get("metadata_json", {}).get("parsed", {})
                    if "language" in parsed_data:
                        lang = parsed_data["language"]
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                        used_parsers.add(f"{lang.title()} Parser")
                    elif "type" in parsed_data:
                        config_type = parsed_data["type"]
                        used_parsers.add(f"{config_type.title()} Config Parser")
                        
                    # 프레임워크/자격 요건 감지 (is_ 계열 boolean 플래그 추출)
                    for key, val in parsed_data.items():
                        if key.startswith("is_") and val is True:
                            framework_name = key.replace("is_", "").replace("_", " ").title()
                            detected_frameworks.add(framework_name)
                    
                    # 그래프 분석용 데이터 수집 (주요 언어 대상)
                    if path.endswith(('.kt', '.kts', '.java', '.py', '.js', '.ts', '.jsx', '.tsx', '.cpp', '.c', '.h', '.cc', '.go', '.rs', '.swift', '.rb', '.php', '.cs', '.dart')):
                        all_meta[path] = meta
                    
                    line_count = meta.get("line_count", 0)
                    keywords = meta.get("keywords", [])
                    metadata_json = meta.get("metadata_json", {})

                    # DB에 즉시 추가 (메모리 효율적 저장)
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
                
                # 3.1 GitHub 언어 통계 가져오기 (마이페이지 최적화용)
                try:
                    repo_path = request.repo_url.replace("https://github.com/", "").replace(".git", "").strip("/")
                    repo = fetcher.g.get_repo(repo_path)
                    project.languages = repo.get_languages()
                except Exception as lang_err:
                    print(f"Failed to fetch repo languages: {lang_err}")
                
                # --- [Project Insight DB 저장] ---
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

                # 기존 인사이트 덮어쓰기
                db_session.query(ProjectInsight).filter(ProjectInsight.project_id == project.id).delete()
                
                insight = ProjectInsight(
                    project_id=project.id,
                    tech_stack=tech_stack_json,
                    summary=insight_summary
                )
                db_session.add(insight)
                
                # 4. 의존성 그래프 분석
                q.put("📊 Analyzing dependency graph...")
                builder = DependencyGraphBuilder()
                graph = builder.build_graph(all_meta)
                graph_data = nx.node_link_data(graph)
                
                # 프로젝트 그래프 정보 업데이트
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
                
                # 원자적 트랜잭션 커밋
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
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
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
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
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
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    # Soft delete
    chat_session.is_deleted = 1
    db.commit()
    
    return {"status": "success", "message": "Chat session deleted successfully."}

@app.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
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
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
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
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    if chat_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
    project = chat_session.project
    if not project:
        raise HTTPException(status_code=404, detail="관련 프로젝트를 찾을 수 없습니다.")

    # 1. 엔진 가져오기 또는 로드
    engine = engine_cache.get(session_id)
    
    # 모델 변경 요청이 있거나 캐시된 엔진이 없는 경우 새로 생성
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
        # 2. 질문 저장
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=query
        )
        db.add(user_message)
        
        # 3. RAG 엔진 실행 (언어 추가)
        result = engine.ask(query, language=request.language)
        answer = result.get("answer", "Sorry, I couldn't generate an answer.")
        sources = result.get("sources", [])
        
        # 4. 답변 저장
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            sources=sources
        )
        db.add(assistant_message)

        # 5. 첫 질문인 경우 제목 요약
        is_first_msg = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count() == 1 # 방금 add한 user_message만 있어야함
        if is_first_msg:
            try:
                new_title = engine.summarize_title(query)
                chat_session.title = new_title
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
        
        # 생성된 코드를 DB에 캐싱
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
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    
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
        # 각 프로젝트의 최신 세션 및 인사이트 가져오기
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
        
    # 1. 캐시 확인
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
        
        readme_content = engine.generate_readme(
            request.user_inputs, 
            llm=temp_llm, 
            provider=request.provider, 
            model_name=request.model_name,
            languages=request.languages
        )
        
        # 항상 새로운 버전을 생성
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
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
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
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
    project = chat_session.project
    if not project or not project.graph_data:
        raise HTTPException(status_code=404, detail="프로젝트 그래프 정보를 찾을 수 없습니다.")
        
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
        
    # 언어 설정 (사용자 국가 기반)
    language = "English"
    if current_user.country == "South Korea":
        language = "Korean"
        
    try:
        analysis = engine.analyze_architecture(language=language)
        return {"analysis": analysis}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))