from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class PythonParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "python",
            "imports": [],             # import os, from x import y
            "classes": [],             # 클래스 (상속, 메서드, 데코레이터 포함)
            "functions": [],           # 모듈 레벨 함수
            "is_ai_or_data_project": False, # PyTorch, Pandas 등 감지
            "is_web_backend": False         # FastAPI, Django 등 감지
        }

        # 파이썬 문법에 최적화된 Tree-sitter Query
        query_source = """
        ;; 1. Import 구문 캡처 (import X, from X import Y)
        (import_statement) @import_stmt
        (import_from_statement) @import_from_stmt

        ;; 2. Class 및 Function 선언 캡처
        (class_definition name: (identifier) @class_name) @class_node
        (function_definition name: (identifier) @func_name) @func_node
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                
                # --- 1. Imports ---
                if capture_name in ["import_stmt", "import_from_stmt"]:
                    # AST 노드 전체 텍스트를 추출 (예: 'from src.models import User')
                    import_text = node.text.decode('utf8', errors='ignore').strip()
                    parsed_data["imports"].append(import_text)

                    # 생태계 추론 로직 (AI vs Web)
                    lower_text = import_text.lower()
                    if any(pkg in lower_text for pkg in ["torch", "tensorflow", "pandas", "numpy", "scikit"]):
                        parsed_data["is_ai_or_data_project"] = True
                    if any(pkg in lower_text for pkg in ["fastapi", "django", "flask", "starlette"]):
                        parsed_data["is_web_backend"] = True

                # --- 2. Classes ---
                elif capture_name == "class_node":
                    class_info = self._process_class(node)
                    parsed_data["classes"].append(class_info)

                # --- 3. Functions (모듈 레벨) ---
                elif capture_name == "func_node":
                    # 클래스 내부에 있는 메서드(Method)는 모듈 레벨 함수에서 제외
                    if not self._is_method(node):
                        func_info = self._process_function(node)
                        parsed_data["functions"].append(func_info)

        except Exception as e:
            meta["error"] = f"Python 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_class(self, node) -> Dict[str, Any]:
        """클래스의 이름, 상속, 데코레이터, Docstring, 내부 메서드를 추출합니다."""
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"
        
        # 상속 (superclasses)
        inherits = []
        superclasses_node = node.child_by_field_name("superclasses")
        if superclasses_node:
            # (A, B) 형태에서 식별자만 추출
            for child in superclasses_node.children:
                if child.type in ["identifier", "attribute"]:
                    inherits.append(child.text.decode('utf8', errors='ignore'))

        # 내부 메서드 수집
        methods = []
        body_node = node.child_by_field_name("body")
        if body_node:
            for child in body_node.children:
                if child.type == "function_definition":
                    m_name = child.child_by_field_name("name")
                    if m_name:
                        methods.append(m_name.text.decode('utf8', errors='ignore'))

        return {
            "name": name,
            "inherits": inherits,
            "decorators": self._extract_decorators(node),
            "methods": methods,
            "docstring": self._extract_docstring(node)
        }

    def _process_function(self, node) -> Dict[str, Any]:
        """함수의 이름, 데코레이터, Docstring을 추출합니다."""
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"
        
        return {
            "name": name,
            "decorators": self._extract_decorators(node),
            "docstring": self._extract_docstring(node)
        }

    def _is_method(self, node) -> bool:
        """현재 함수 노드가 클래스 내부에 속해 있는지 확인합니다."""
        parent = node.parent
        while parent:
            if parent.type == "class_definition":
                return True
            parent = parent.parent
        return False

    def _extract_decorators(self, node) -> List[str]:
        """
        파이썬의 Tree-sitter는 데코레이터가 붙은 함수/클래스를 'decorated_definition'으로 감쌉니다.
        이를 역추적하여 @app.get("/items") 같은 데코레이터 구문을 통째로 추출합니다.
        """
        decorators = []
        parent = node.parent
        if parent and parent.type == "decorated_definition":
            for child in parent.children:
                if child.type == "decorator":
                    decorators.append(child.text.decode('utf8', errors='ignore'))
        return decorators

    def _extract_docstring(self, node) -> str:
        """
        파이썬의 Docstring은 주석(comment)이 아니라, 
        블록(body) 내부의 첫 번째 문자열 표현식(expression_statement -> string)입니다.
        """
        body_node = node.child_by_field_name("body")
        if body_node and len(body_node.children) > 0:
            first_stmt = body_node.children[0]
            if first_stmt.type == "expression_statement":
                for child in first_stmt.children:
                    if child.type == "string":
                        # 따옴표(""") 및 앞뒤 공백 제거
                        return child.text.decode('utf8', errors='ignore').strip('\'" \n\t')
        return ""