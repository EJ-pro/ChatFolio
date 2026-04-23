from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class SwiftParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "language": "swift",
            "imports": [],             # e.g., import UIKit, SwiftUI
            "protocols": [],           # protocol declarations
            "classes": [],             # class declarations
            "structs": [],             # struct declarations
            "enums": [],               # enum declarations
            "is_swiftui": False        # Whether this is a SwiftUI View
        }

        # 1. Tree-sitter Query for Swift syntax
        query_source = """
        ;; 1. Extract imports
        (import_declaration (type_identifier) @import_name)
        (import_declaration (path_component (identifier) @import_name))

        ;; 2. Extract Protocol, Class, Struct, Enum declarations
        (protocol_declaration (type_identifier) @protocol_name) @protocol_node
        (class_declaration (type_identifier) @class_name) @class_node
        (struct_declaration (type_identifier) @struct_name) @struct_node
        (enum_declaration (type_identifier) @enum_name) @enum_node

        ;; 3. Extract inheritance and protocol adoption
        (type_inheritance_clause (type_identifier) @inherited_type)

        ;; 4. Extract function and method declarations
        (function_declaration (simple_identifier) @func_name) @func_node
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')

                # --- 1. Imports ---
                if capture_name == "import_name":
                    if node_text not in parsed_data["imports"]:
                        parsed_data["imports"].append(node_text)
                    if node_text == "SwiftUI":
                        parsed_data["is_swiftui"] = True

                # --- 2. Protocols, Classes, Structs, Enums ---
                elif capture_name in ["protocol_name", "class_name", "struct_name", "enum_name"]:
                    category = capture_name.split('_')[0] + "s" # e.g., classes, structs
                    parsed_data[category].append(self._process_swift_node(node.parent, category[:-1]))

                # --- 3. SwiftUI Detection (whether View protocol is adopted) ---
                elif capture_name == "inherited_type":
                    if node_text == "View":
                        parsed_data["is_swiftui"] = True

        except Exception as e:
            meta["error"] = f"Error during Swift parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_swift_node(self, node, node_type: str) -> Dict[str, Any]:
        """Analyze the internal structure of a Swift type (Class, Struct, etc.)."""
        # Extract name
        name = "Unknown"
        for child in node.children:
            if child.type == "type_identifier":
                name = child.text.decode('utf8', errors='ignore')
                break

        # Extract inheritance/adoption
        inherits = []
        inheritance_clause = None
        for child in node.children:
            if child.type == "type_inheritance_clause":
                inheritance_clause = child
                break
        
        if inheritance_clause:
            for child in inheritance_clause.children:
                if child.type == "type_identifier":
                    inherits.append(child.text.decode('utf8', errors='ignore'))

        # Extract internal methods
        methods = []
        # Swift has complex nesting, so find method declarations by simple children traversal
        body = None
        for child in node.children:
            if child.type in ["class_body", "struct_body", "enum_body", "protocol_body"]:
                body = child
                break
        
        if body:
            for child in body.children:
                if child.type == "function_declaration":
                    # Find function name node
                    for sub in child.children:
                        if sub.type == "simple_identifier":
                            methods.append(sub.text.decode('utf8', errors='ignore'))

        return {
            "name": name,
            "type": node_type,
            "inherits": inherits,
            "methods": methods,
            "docstring": self._extract_docstring(node)
        }

    def _extract_docstring(self, node) -> str:
        """Extract Swift doc comments (/// or /** */)."""
        if not node or not node.prev_sibling:
            return ""
        comments = []
        current = node.prev_sibling
        while current and current.type in ["comment", "multiline_comment"]:
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
        return "\n".join(reversed(comments)) if comments else ""
