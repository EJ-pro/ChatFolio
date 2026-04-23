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
    country = Column(String, nullable=True) # User country
    job = Column(String, nullable=True) # User occupation
    persona_data = Column(JSONB, nullable=True) # Developer MBTI (Persona) data
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="user", cascade="all, delete")
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete")
    token_usages = relationship("TokenUsage", back_populates="user", cascade="all, delete")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # nullable=True for backward compatibility
    repo_url = Column(String, index=True)
    file_count = Column(Integer)
    node_count = Column(Integer)
    edge_count = Column(Integer)
    graph_data = Column(JSONB, nullable=True) # Serialized NetworkX graph
    mermaid_code = Column(Text, nullable=True) # Cached generated Mermaid diagram
    status = Column(String, default="COMPLETED") # Analysis status
    languages = Column(JSONB, nullable=True) # GitHub language statistics (bytes)
    last_commit_hash = Column(String, nullable=True)
    last_commit_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="projects")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete")
    sessions = relationship("ChatSession", back_populates="project", cascade="all, delete")
    readmes = relationship("GeneratedReadme", back_populates="project", cascade="all, delete")
    insight = relationship("ProjectInsight", back_populates="project", uselist=False, cascade="all, delete")

class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    file_path = Column(String, index=True)
    content = Column(Text)
    content_summary = Column(Text, nullable=True) # Summary
    importance_score = Column(Integer, default=0) # Based on reference count
    keywords = Column(JSONB, nullable=True)
    line_count = Column(Integer, default=0)
    file_size = Column(Integer, default=0)
    metadata_json = Column(JSONB, nullable=True)

    project = relationship("Project", back_populates="files")

class GeneratedReadme(Base):
    __tablename__ = "generated_readmes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    content = Column(Text)
    template_type = Column(String, default="default")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="readmes")

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
    title = Column(String, default="New Chat")
    is_deleted = Column(Integer, default=0) # 0: Active, 1: Deleted
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
    sources = Column(JSONB, nullable=True) # Sources referenced by AI (JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")

class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="inquiries")

class TokenUsage(Base):
    __tablename__ = "token_usages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    model_name = Column(String, index=True)
    feature_name = Column(String, index=True) # 'Chat', 'Analyze', 'Readme', 'Architecture', 'Interview'
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="token_usages")

import time
from sqlalchemy.exc import OperationalError

# Table initialization function
def init_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            # [Migration Hack] Manually add columns if they do not exist
            from sqlalchemy import text
            with engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS persona_data JSONB"))
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS country VARCHAR"))
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS job VARCHAR"))
                    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS languages JSONB"))
                    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_commit_hash VARCHAR"))
                    conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_commit_message TEXT"))
                    # Add ProjectFile columns
                    conn.execute(text("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS keywords JSONB"))
                    conn.execute(text("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS line_count INTEGER DEFAULT 0"))
                    conn.execute(text("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS file_size INTEGER DEFAULT 0"))
                    conn.execute(text("ALTER TABLE project_files ADD COLUMN IF NOT EXISTS metadata_json JSONB"))
                    # Add ChatSession columns
                    conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS title VARCHAR DEFAULT 'New Chat'"))
                    conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS is_deleted INTEGER DEFAULT 0"))
                    # Drop unique constraint on generated_readmes if exists (for migration to multi-readme history)
                    conn.execute(text("ALTER TABLE generated_readmes DROP CONSTRAINT IF EXISTS generated_readmes_project_id_key"))
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
