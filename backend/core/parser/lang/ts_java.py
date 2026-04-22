from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class JavaParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "language": "java",
            "package": None,
            "imports": [],
            "classes": [],
            "interfaces": [],
            "is_spring_boot": False
        }

        # 1. Java 문법에 맞춘 Tree-sitter Query
        query_source = """
        ;; 1. 패키지 이름 추출
        (package_declaration (scoped_identifier) @package_name)

        ;; 2. Import 추출
        (import_declaration (scoped_identifier) @import_path)

        ;; 3. 클래스 및 인터페이스 선언 추출
        (class_declaration 
            name: (identifier) @class_name
            interfaces: (interfaces (type_list (type_identifier) @base_interface))?
        ) @class_node

        (interface_declaration
            name: (identifier) @interface_name
        ) @interface_node

        ;; 4. 어노테이션 추출 (Spring Boot 등 판별용)
        (marker_annotation name: (identifier) @annotation)
        (normal_annotation name: (identifier) @annotation)
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')

                if capture_name == "package_name":
                    parsed_data["package"] = node_text
                elif capture_name == "import_path":
                    parsed_data["imports"].append(node_text)
                    if "org.springframework" in node_text:
                        parsed_data["is_spring_boot"] = True
                
                elif capture_name == "class_node":
                    parsed_data["classes"].append(self._process_java_node(node, "class"))
                elif capture_name == "interface_node":
                    parsed_data["interfaces"].append(self._process_java_node(node, "interface"))

                elif capture_name == "annotation":
                    if node_text in ["SpringBootApplication", "RestController", "Service", "Repository"]:
                        parsed_data["is_spring_boot"] = True

        except Exception as e:
            meta["error"] = f"Java 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_java_node(self, node, node_type: str) -> Dict[str, Any]:
        """Java 클래스/인터페이스 내부를 분석합니다."""
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"

        # 메서드 추출
        methods = []
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "method_declaration":
                    m_name_node = child.child_by_field_name("name")
                    if m_name_node:
                        methods.append(m_name_node.text.decode('utf8', errors='ignore'))

        return {
            "name": name,
            "type": node_type,
            "methods": methods,
            "docstring": self._extract_docstring(node)
        }

    def _extract_docstring(self, node) -> str:
        if not node or not node.prev_sibling:
            return ""
        comments = []
        current = node.prev_sibling
        while current and current.type in ["comment", "block_comment"]:
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
        return "\n".join(reversed(comments)) if comments else ""