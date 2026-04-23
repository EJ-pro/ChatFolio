from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class PhpParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "language": "php",
            "namespace": None,
            "uses": [],                # use Namespace\Class;
            "classes": [],             # class, trait, interface
            "functions": [],           # global functions
            "is_laravel": False,
            "is_wordpress": False
        }

        # 1. Tree-sitter Query for PHP syntax
        query_source = """
        ;; 1. Extract namespace definitions
        (namespace_definition (namespace_name) @namespace_name)

        ;; 2. Extract use statements (imports)
        (namespace_use_declaration (namespace_use_clause (qualified_name) @use_name))

        ;; 3. Extract class, interface, and trait declarations
        (class_declaration name: (name) @class_name) @class_node
        (interface_declaration name: (name) @interface_name) @interface_node
        (trait_declaration name: (name) @trait_name) @trait_node

        ;; 4. Extract function and method declarations
        (function_declaration name: (name) @func_name) @func_node
        (method_declaration name: (name) @method_name) @method_node
        """

        try:
            # Check text if no <?php tag, as the Tree-sitter PHP parser may not work well without it
            if "<?php" not in self.content and "<?=" not in self.content:
                # If this is a template file or not a pure logic file
                pass

            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')

                # --- 1. Namespace & Uses ---
                if capture_name == "namespace_name":
                    parsed_data["namespace"] = node_text
                elif capture_name == "use_name":
                    parsed_data["uses"].append(node_text)
                    # Detect Laravel framework
                    if "Illuminate\\" in node_text:
                        parsed_data["is_laravel"] = True

                # --- 2. Classes, Interfaces, Traits ---
                elif capture_name in ["class_name", "interface_name", "trait_name"]:
                    type_str = capture_name.split('_')[0]
                    parsed_data["classes"].append(self._process_php_node(node.parent, type_str))

                # --- 3. Global Functions ---
                elif capture_name == "func_name":
                    # Extract only global functions outside of classes
                    if self._is_global_scope(node):
                        parsed_data["functions"].append({
                            "name": node_text,
                            "docstring": self._extract_docstring(node.parent)
                        })
                
                # --- 4. WordPress detection hints ---
                if "wp_" in node_text or "add_action" in node_text:
                    parsed_data["is_wordpress"] = True

        except Exception as e:
            meta["error"] = f"Error during PHP parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_php_node(self, node, node_type: str) -> Dict[str, Any]:
        """Analyze the internal structure of a PHP class, interface, or trait."""
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"

        # Analyze inheritance and implementation
        inherits = []
        extends_node = node.child_by_field_name("extends")
        if extends_node:
            inherits.append(extends_node.text.decode('utf8', errors='ignore').replace('extends', '').strip())
        
        implements_node = node.child_by_field_name("implements")
        if implements_node:
            inherits.append(implements_node.text.decode('utf8', errors='ignore').replace('implements', '').strip())

        # Extract methods
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
            "inherits": inherits,
            "methods": methods,
            "docstring": self._extract_docstring(node)
        }

    def _is_global_scope(self, node) -> bool:
        """Check whether a node is in global scope, not inside a class or method."""
        curr = node.parent
        while curr:
            if curr.type in ["class_declaration", "interface_declaration", "trait_declaration"]:
                return False
            curr = curr.parent
        return True

    def _extract_docstring(self, node) -> str:
        """Extract PHPDoc (/** ... */) or regular comments."""
        if not node or not node.prev_sibling:
            return ""
        comments = []
        current = node.prev_sibling
        while current and current.type in ["comment"]:
            text = current.text.decode('utf8', errors='ignore').strip()
            comments.append(text)
            current = current.prev_sibling
        return "\n".join(reversed(comments)) if comments else ""
