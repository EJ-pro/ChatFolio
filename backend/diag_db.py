import sys
import os
sys.path.append('.')
from database.session import SessionLocal
from database.models import Project, ProjectFile
import json

def check_db():
    db = SessionLocal()
    p = db.query(Project).order_by(Project.id.desc()).first()
    if not p:
        print("No project found.")
        return

    print(f"Project ID: {p.id}")
    print(f"Repo: {p.repo_url}")
    print(f"Node count: {p.node_count}")
    print(f"Edge count: {p.edge_count}")

    files = db.query(ProjectFile).filter(ProjectFile.project_id == p.id).limit(10).all()
    for f in files:
        parsed = f.metadata_json.get('parsed', {}) if f.metadata_json else {}
        lang = parsed.get('language', 'Unknown')
        imports = parsed.get('imports', [])
        print(f"File: {f.file_path}")
        print(f"  Lang: {lang}")
        print(f"  Imports({len(imports)}): {imports[:3]}...")
    
    db.close()

if __name__ == "__main__":
    check_db()
