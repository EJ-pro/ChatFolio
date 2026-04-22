from backend.database.session import SessionLocal
from backend.models.models import Project

db = SessionLocal()
p = db.query(Project).order_by(Project.id.desc()).first()
print(f"Project ID: {p.id}")
print(f"Node count: {p.node_count}")
print(f"Edge count: {p.edge_count}")

# Print first 200 chars of graph_data
import json
print(json.dumps(p.graph_data)[:200])
