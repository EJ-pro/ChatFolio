from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class KotlinParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        # 부모 클래스의 기본 메타데이터 추출
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "language": "kotlin",
            "package": None,
            "imports": [],
            "classes": [],             # class, object, interface
            "functions": [],           # top-level functions
            "has_android_resource": False
        }

        # 1. Kotlin 문법에 맞춘 Tree-sitter Query
        query_source = """
        ;; 1. 패키지 선언 추출
        (package_header (identifier) @package_name)

        ;; 2. Import 구문 추출
        (import_header (identifier) @import_path)

        ;; 3. 클래스 및 객체 선언부 추출 (상속 포함)
        (class_declaration
            (type_identifier) @class_name
            (delegation_specifier (user_type (type_identifier) @base_class))?
        ) @class_node
        
        (object_declaration
            (identifier) @object_name
        ) @object_node

        ;; 4. 인터페이스 선언 추출
        (interface_declaration
            (type_identifier) @interface_name
        ) @interface_node

        ;; 5. 함수 선언부 추출
        (function_declaration
            (simple_identifier) @func_name
        ) @func_node
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')

                # --- 1. Package & Imports ---
                if capture_name == "package_name":
                    parsed_data["package"] = node_text
                elif capture_name == "import_path":
                    parsed_data["imports"].append(node_text)
                    if "android." in node_text:
                        parsed_data["has_android_resource"] = True

                # --- 2. Classes & Objects ---
                elif capture_name == "class_node":
                    class_info = self._process_kotlin_class(node, "class")
                    parsed_data["classes"].append(class_info)
                elif capture_name == "object_node":
                    class_info = self._process_kotlin_class(node, "object")
                    parsed_data["classes"].append(class_info)
                elif capture_name == "interface_node":
                    class_info = self._process_kotlin_class(node, "interface")
                    parsed_data["classes"].append(class_info)

                # --- 3. Top-level Functions ---
                elif capture_name == "func_node":
                    # 클래스 멤버가 아닌 최상위 함수만 추출 (단순 구현: 부모가 소스파일인 경우)
                    if node.parent and node.parent.type == "source_file":
                        parsed_data["functions"].append({
                            "name": node_text,
                            "docstring": self._extract_docstring(node)
                        })

        except Exception as e:
            meta["error"] = f"Kotlin 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_kotlin_class(self, node, class_type: str) -> Dict[str, Any]:
        """클래스 내부 구조(메서드, 상속)를 분석합니다."""
        # 이름 추출 (Kotlin은 type_identifier 혹은 simple_identifier 사용)
        name = "Unknown"
        for child in node.children:
            if child.type in ["type_identifier", "identifier"]:
                name = child.text.decode('utf8', errors='ignore')
                break

        # 상속 관계 추출
        inherits = []
        for child in node.children:
            if child.type == "delegation_specifier":
                inherits.append(child.text.decode('utf8', errors='ignore'))

        # 메서드 추출 (body 내부 탐색)
        methods = []
        body = None
        for child in node.children:
            if child.type == "class_body":
                body = child
                break
        
        if body:
            for child in body.children:
                if child.type == "function_declaration":
                    # 함수 이름 노드 찾기
                    for sub in child.children:
                        if sub.type == "simple_identifier":
                            methods.append(sub.text.decode('utf8', errors='ignore'))

        return {
            "name": name,
            "type": class_type,
            "inherits": inherits,
            "methods": methods,
            "docstring": self._extract_docstring(node)
        }

    def _extract_docstring(self, node) -> str:
        if not node or not node.prev_sibling:
            return ""
        
        comments = []
        current = node.prev_sibling
        while current and current.type in ["comment", "kdoc"]:
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
            
        return "\n".join(reversed(comments)) if comments else ""
