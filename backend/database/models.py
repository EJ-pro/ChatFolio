from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base, engine

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    repo_url = Column(String, index=True)
    file_count = Column(Integer)
    node_count = Column(Integer)
    edge_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

import time
from sqlalchemy.exc import OperationalError

# 테이블 생성 함수
def init_db():
    retries = 5
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            print("Database initialized successfully.")
            break
        except OperationalError:
            retries -= 1
            print(f"Database not ready. Retrying... ({retries} left)")
            time.sleep(2)
    else:
        print("Could not connect to the database.")
