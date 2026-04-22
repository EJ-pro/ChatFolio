from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class GoParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "go",
            "is_main_package": False,  # 실행 가능한 엔트리포인트(main) 여부
            "imports": [],             # import "fmt" 등
            "structs": {},             # 구조체 및 연결된 메서드
            "interfaces": {},          # 인터페이스 선언
            "functions": [],           # 일반 전역 함수
            "goroutine_count": 0       # go 키워드 사용 횟수 (동시성 지표)
        }

        # 1. Go 문법에 맞춘 Tree-sitter Query
        query_source = """
        ;; 1. 패키지 이름 캡처
        (package_clause (package_identifier) @package_name)

        ;; 2. Import 경로 캡처
        (import_spec path: (interpreted_string_literal) @import_path)

        ;; 3. 구조체(Struct) 및 인터페이스(Interface) 캡처
        (type_spec name: (type_identifier) @type_name type: (struct_type)) @struct_node
        (type_spec name: (type_identifier) @type_name type: (interface_type)) @interface_node

        ;; 4. 함수(Function) 및 메서드(Method) 선언부 캡처
        (function_declaration name: (identifier) @func_name) @func_node
        (method_declaration name: (identifier) @method_name) @method_node

        ;; 5. 동시성(Goroutine) 구문 캡처
        (go_statement) @go_stmt
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            # 메서드들을 임시로 저장할 딕셔너리 (struct_name: [methods])
            temp_methods = {}

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')
                
                # --- 1. Package Name ---
                if capture_name == "package_name":
                    if node_text == "main":
                        parsed_data["is_main_package"] = True

                # --- 2. Imports ---
                elif capture_name == "import_path":
                    parsed_data["imports"].append(node_text.strip('"'))

                # --- 3. Structs ---
                elif capture_name == "struct_node":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = name_node.text.decode('utf8', errors='ignore')
                        docstring = self._extract_docstring(node.parent)
                        parsed_data["structs"][name] = {
                            "name": name,
                            "methods": temp_methods.get(name, []),
                            "docstring": docstring
                        }

                # --- 4. Interfaces ---
                elif capture_name == "interface_node":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        name = name_node.text.decode('utf8', errors='ignore')
                        methods = self._extract_interface_methods(node.child_by_field_name("type"))
                        docstring = self._extract_docstring(node.parent)
                        parsed_data["interfaces"][name] = {
                            "name": name,
                            "methods": methods,
                            "docstring": docstring
                        }

                # --- 5. Global Functions ---
                elif capture_name == "func_node":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        parsed_data["functions"].append({
                            "name": name_node.text.decode('utf8', errors='ignore'),
                            "docstring": self._extract_docstring(node)
                        })

                # --- 6. Methods (리시버 연결) ---
                elif capture_name == "method_node":
                    receiver_type = self._get_receiver_base_type(node)
                    name_node = node.child_by_field_name("name")
                    if receiver_type and name_node:
                        m_name = name_node.text.decode('utf8', errors='ignore')
                        if receiver_type in parsed_data["structs"]:
                            parsed_data["structs"][receiver_type]["methods"].append(m_name)
                        else:
                            # 구조체 정의보다 메서드가 먼저 나왔거나 다른 파일에 있을 가능성 대비
                            if receiver_type not in temp_methods:
                                temp_methods[receiver_type] = []
                            temp_methods[receiver_type].append(m_name)

                # --- 7. Goroutines ---
                elif capture_name == "go_stmt":
                    parsed_data["goroutine_count"] += 1

        except Exception as e:
            meta["error"] = f"Go 파싱 중 오류 발생: {str(e)}"

        # 딕셔너리를 리스트로 변환하여 최종 JSON 규격화
        parsed_data["structs"] = list(parsed_data["structs"].values())
        parsed_data["interfaces"] = list(parsed_data["interfaces"].values())
        
        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _get_receiver_base_type(self, method_node) -> str:
        """
        메서드의 리시버(Receiver)에서 기본 구조체 이름을 추출합니다.
        예: `func (s *Server) Start()` -> `Server` 반환
        """
        receiver_list = method_node.child_by_field_name("receiver")
        if not receiver_list: return None
        
        for child in receiver_list.children:
            if child.type == "parameter_declaration":
                type_node = child.child_by_field_name("type")
                if not type_node: continue
                
                # 포인터 리시버 (*Server)
                if type_node.type == "pointer_type":
                    for pt_child in type_node.children:
                        if pt_child.type == "type_identifier":
                            return pt_child.text.decode('utf8', errors='ignore')
                # 값 리시버 (Server)
                elif type_node.type == "type_identifier":
                    return type_node.text.decode('utf8', errors='ignore')
        return None

    def _extract_interface_methods(self, interface_type_node) -> List[str]:
        """인터페이스 내부에 정의된 메서드 시그니처 이름을 추출합니다."""
        methods = []
        if not interface_type_node: return methods
        for child in interface_type_node.children:
            if child.type == "method_elem":
                name_node = child.child_by_field_name("name")
                if name_node:
                    methods.append(name_node.text.decode('utf8', errors='ignore'))
        return methods

    def _extract_docstring(self, node) -> str:
        if not node or not node.prev_sibling: return ""
        comments = []
        current = node.prev_sibling
        while current and current.type == "comment":
            # Go의 주석은 보통 // 를 사용합니다.
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
        return "\n".join(reversed(comments)) if comments else ""