from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base, engine
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True) # 'github' or 'google'
    email = Column(String, unique=True, index=True, nullable=True)
    name = Column(String)
    github_username = Column(String, unique=True, index=True, nullable=True)
    github_token = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    persona_data = Column(JSONB, nullable=True) # 개발자 MBTI (Persona) 데이터 저장
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="user", cascade="all, delete")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # 기존 데이터 호환을 위해 nullable=True
    repo_url = Column(String, index=True)
    file_count = Column(Integer)
    node_count = Column(Integer)
    edge_count = Column(Integer)
    graph_data = Column(JSONB, nullable=True) # 직렬화된 NetworkX 그래프 저장
    mermaid_code = Column(Text, nullable=True) # 생성된 Mermaid 다이어그램 캐싱
    status = Column(String, default="COMPLETED") # 분석 상태
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete")
    sessions = relationship("ChatSession", back_populates="project", cascade="all, delete")
    readme = relationship("GeneratedReadme", back_populates="project", uselist=False, cascade="all, delete")
    insight = relationship("ProjectInsight", back_populates="project", uselist=False, cascade="all, delete")

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    file_path = Column(String, index=True)
    content = Column(Text)
    content_summary = Column(Text, nullable=True) # 요약본
    importance_score = Column(Integer, default=0) # 참조 횟수 기반

    project = relationship("Project", back_populates="files")

class GeneratedReadme(Base):
    __tablename__ = "generated_readmes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), unique=True)
    content = Column(Text)
    template_type = Column(String, default="default")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="readme")

class ProjectInsight(Base):
    __tablename__ = "project_insights"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), unique=True)
    tech_stack = Column(JSONB, nullable=True)
    summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="insight")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    provider = Column(String, default="groq")
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    project = relationship("Project", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role = Column(String) # 'user' or 'assistant'
    content = Column(Text)
    sources = Column(JSONB, nullable=True) # AI가 참고한 출처 (JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")

import time
from sqlalchemy.exc import OperationalError

# 테이블 생성 함수
def init_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            # [Migration Hack] persona_data 컬럼이 없는 경우 수동 추가
            from sqlalchemy import text
            with engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS persona_data JSONB"))
                    conn.commit()
                except Exception as e:
                    print(f"Migration error: {e}")
            print("Database initialized successfully.")
            break
        except OperationalError:
            retries -= 1
            print(f"Database not ready. Retrying... ({retries} left)")
            time.sleep(2)
    else:
        print("Could not connect to the database.")
