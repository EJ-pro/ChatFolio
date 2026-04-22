from core.parser.lang.ts_python import PythonParser

content = """
import os
from database.database import SessionLocal
from core.graph.graph_builder import DependencyGraphBuilder

class Test:
    pass
"""

parser = PythonParser(content, "test.py")
result = parser.parse()
parsed = result.get("metadata_json", {}).get("parsed", {})

print(f"Language: {parsed.get('language')}")
print(f"Imports: {parsed.get('imports')}")
print(f"Classes: {[c['name'] for c in parsed.get('classes', [])]}")
