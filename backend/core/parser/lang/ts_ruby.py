from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class RubyParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "language": "ruby",
            "requires": [],            # require '...' or require_relative '...'
            "modules": [],             # module Name
            "classes": [],             # class Name < Base
            "methods": [],             # top-level methods (singleton or global)
            "is_rails": False          # Whether this is a Ruby on Rails project
        }

        # 1. Tree-sitter Query for Ruby syntax
        query_source = """
        ;; 1. Extract Require (dependencies)
        (call
          method: (identifier) @method_name (#match? @method_name "^require(_relative)?$")
          arguments: (argument_list (string (string_content) @req_path))
        )

        ;; 2. Extract Module definitions
        (module
          name: [
            (constant) @module_name
            (scope_resolution) @module_name
          ]
        ) @module_node

        ;; 3. Extract Class definitions and inheritance
        (class
          name: [
            (constant) @class_name
            (scope_resolution) @class_name
          ]
          superclass: (superclass [
            (constant) @base_class
            (scope_resolution) @base_class
          ])?
        ) @class_node

        ;; 4. Extract Method definitions
        (method name: (identifier) @method_name) @method_node

        ;; 5. Extract Singleton Methods (self.method)
        (singleton_method name: (identifier) @method_name) @method_node
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')

                # --- 1. Requires ---
                if capture_name == "req_path":
                    parsed_data["requires"].append(node_text)
                    # Detect Rails-related libraries
                    if "rails" in node_text or "active_record" in node_text:
                        parsed_data["is_rails"] = True

                # --- 2. Modules ---
                elif capture_name == "module_name":
                    # Check parent node to prevent duplicates
                    parsed_data["modules"].append({
                        "name": node_text,
                        "docstring": self._extract_docstring(node.parent)
                    })

                # --- 3. Classes & Inheritance ---
                elif capture_name == "class_name":
                    class_info = self._process_ruby_class(node.parent)
                    parsed_data["classes"].append(class_info)
                    
                    # Check whether Rails Base Class is inherited
                    if any("ApplicationRecord" in b or "ActiveRecord" in b for b in class_info["inherits"]):
                        parsed_data["is_rails"] = True

                # --- 4. Methods ---
                elif capture_name == "method_node":
                    # Extract only global methods not inside a class or module
                    if self._is_global_scope(node):
                        method_name_node = node.child_by_field_name("name")
                        if method_name_node:
                            parsed_data["methods"].append({
                                "name": method_name_node.text.decode('utf8', errors='ignore'),
                                "docstring": self._extract_docstring(node)
                            })

        except Exception as e:
            meta["error"] = f"Error during Ruby parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_ruby_class(self, node) -> Dict[str, Any]:
        """Analyze inheritance relationships and methods inside a Ruby class."""
        # Extract name
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"

        # Extract inheritance (superclass)
        inherits = []
        superclass_node = node.child_by_field_name("superclass")
        if superclass_node:
            inherits.append(superclass_node.text.decode('utf8', errors='ignore').replace('<', '').strip())

        # Extract methods (traverse children since body field may not be explicit)
        methods = []
        # In Ruby grammar, class body typically has specific types among children
        for child in node.children:
            if child.type == "method":
                m_name_node = child.child_by_field_name("name")
                if m_name_node:
                    methods.append(m_name_node.text.decode('utf8', errors='ignore'))
            elif child.type == "singleton_method":
                m_name_node = child.child_by_field_name("name")
                if m_name_node:
                    methods.append("self." + m_name_node.text.decode('utf8', errors='ignore'))

        return {
            "name": name,
            "inherits": inherits,
            "methods": methods,
            "docstring": self._extract_docstring(node)
        }

    def _is_global_scope(self, node) -> bool:
        """Check whether a method is at the top level, not inside a class or module."""
        curr = node.parent
        while curr:
            if curr.type in ["class", "module"]:
                return False
            curr = curr.parent
        return True

    def _extract_docstring(self, node) -> str:
        """Extract Ruby comments (#) by backtracking."""
        if not node or not node.prev_sibling:
            return ""
        comments = []
        current = node.prev_sibling
        while current and current.type == "comment":
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
        return "\n".join(reversed(comments)) if comments else ""
