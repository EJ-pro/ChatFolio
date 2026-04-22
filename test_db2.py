import sys
import os

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.append(backend_path)

from backend.database.session import SessionLocal
from backend.models.models import Project

def main():
    db = SessionLocal()
    p = db.query(Project).order_by(Project.id.desc()).first()
    if p:
        print(f"Project: {p.repo_url}")
        print(f"Node count: {p.node_count}")
        print(f"Edge count: {p.edge_count}")
        print(f"Graph Data: Nodes={len(p.graph_data.get('nodes', []))} Edges={len(p.graph_data.get('edges', []))}")
    else:
        print("No project found.")

if __name__ == "__main__":
    main()
