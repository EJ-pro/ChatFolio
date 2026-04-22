from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class JavaScriptParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "javascript",  # js, ts, jsx, tsx
            "imports": [],             # 참조하는 모듈 목록
            "exports": [],             # 외부로 노출하는 함수/클래스
            "functions": [],           # 내부 함수 (화살표 함수 포함)
            "classes": [],             # ES6 클래스
            "is_react_component": False # JSX(UI) 렌더링 파일 여부
        }

        # JS/TS/JSX 생태계의 자유도를 모두 커버하는 하이브리드 쿼리
        query_source = """
        ;; 1. Imports (ES6 모듈 & CommonJS require 모두 캡처)
        (import_statement source: (string) @import_src)
        (call_expression 
            function: (identifier) @req_func (#eq? @req_func "require")
            arguments: (arguments (string) @require_src)
        )

        ;; 2. Exports (export default, export const 등)
        (export_statement declaration: (_) @export_decl)
        (export_statement value: (_) @export_value)

        ;; 3. Functions (일반 함수 & 화살표 함수 모두 캡처)
        (function_declaration name: (identifier) @func_name)
        (lexical_declaration 
            (variable_declarator 
                name: (identifier) @arrow_func_name 
                value: [(arrow_function) (function)]
            )
        )

        ;; 4. ES6 Classes
        (class_declaration name: (identifier) @class_name)

        ;; 5. JSX 탐지 (React/Next.js 컴포넌트 판별용)
        (jsx_element) @jsx_node
        (jsx_self_closing_element) @jsx_node
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                
                # --- 1. Imports ---
                if capture_name in ["import_src", "require_src"]:
                    # 따옴표 제거 ( 'react' -> react )
                    src = node.text.decode('utf8', errors='ignore').strip("'\"`")
                    if src not in parsed_data["imports"]:
                        parsed_data["imports"].append(src)

                # --- 2. Exports ---
                elif capture_name in ["export_decl", "export_value"]:
                    export_name = self._extract_export_name(node)
                    if export_name and export_name not in parsed_data["exports"]:
                        parsed_data["exports"].append(export_name)

                # --- 3. Functions & Arrow Functions ---
                elif capture_name in ["func_name", "arrow_func_name"]:
                    name = node.text.decode('utf8', errors='ignore')
                    
                    # 화살표 함수의 경우 부모 노드(lexical_declaration) 기준으로 주석을 찾음
                    doc_node = node.parent.parent if capture_name == "arrow_func_name" else node
                    docstring = self._extract_docstring(doc_node)
                    
                    parsed_data["functions"].append({
                        "name": name,
                        "is_arrow": capture_name == "arrow_func_name",
                        "docstring": docstring
                    })

                # --- 4. Classes ---
                elif capture_name == "class_name":
                    name = node.text.decode('utf8', errors='ignore')
                    parsed_data["classes"].append({
                        "name": name,
                        "docstring": self._extract_docstring(node.parent)
                    })

                # --- 5. JSX / React Component Detect ---
                elif capture_name == "jsx_node":
                    # JSX 태그가 단 하나라도 발견되면 이 파일은 화면을 그리는 UI 파일임
                    parsed_data["is_react_component"] = True

        except Exception as e:
            meta["error"] = f"JS/TS 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _extract_export_name(self, node) -> str:
        """
        export const App = () => {} 나 export default App 에서 'App'을 추출합니다.
        자바스크립트는 내보내는 방식이 너무 다양하여 트리 하위를 순회해야 합니다.
        """
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode('utf8', errors='ignore')
            elif child.type in ["function_declaration", "class_declaration"]:
                name_node = child.child_by_field_name("name")
                if name_node:
                    return name_node.text.decode('utf8', errors='ignore')
            elif child.type == "lexical_declaration": # export const ...
                for decl in child.children:
                    if decl.type == "variable_declarator":
                        name_node = decl.child_by_field_name("name")
                        if name_node:
                            return name_node.text.decode('utf8', errors='ignore')
        return None

    def _extract_docstring(self, node) -> str:
        """JSDoc (/** */) 및 일반 주석 추출"""
        if not node or not node.prev_sibling: return ""
        comments = []
        current = node.prev_sibling
        while current and current.type in ["comment", "line_comment", "block_comment"]:
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
        return "\n".join(reversed(comments)) if comments else ""