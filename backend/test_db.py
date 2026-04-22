from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append('.') # Add backend to path

from database.session import SessionLocal
from models.models import Project

db = SessionLocal()
p = db.query(Project).order_by(Project.id.desc()).first()
print('Nodes:', p.node_count, 'Edges:', p.edge_count)
print('Graph Data Nodes:', len(p.graph_data.get('nodes', [])) if p.graph_data else 0)
