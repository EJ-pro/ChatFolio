from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class CppParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        # Extract base metadata from parent class
        meta = self.extract_base_metadata()
        
        # Standard normalized data to send to GraphRAG engine
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "cpp",
            "imports": [],      # e.g., #include <iostream>
            "macros": [],       # e.g., #define MAX_SIZE 100
            "classes": [],      # class, struct
            "functions": [],    # global / namespace functions
        }

        # 1. Define Tree-sitter Query (AST node traversal for C/C++ syntax)
        query_source = """
        ;; 1. Extract includes (system headers <..> and local headers "..")
        (preproc_include path: (_) @include_path)

        ;; 2. Extract macros (#define)
        (preproc_def name: (identifier) @macro_name value: (_)? @macro_val)

        ;; 3. Extract Class and Struct
        (class_specifier name: (type_identifier)? @class_name)
        (struct_specifier name: (type_identifier)? @struct_name)

        ;; 4. Extract Functions (both declarations and definitions)
        (function_definition declarator: (_) @func_name)
        (declaration declarator: (_) @func_name)
        """

        try:
            # Create and execute query using the language object (self.language)
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            current_class_methods = []

            for node, capture_name in captures:
                # Text extraction utility (use utf-8 decoding if not in parent class)
                node_text = node.text.decode('utf8', errors='ignore')

                # --- 1. Imports (#include) ---
                if capture_name == "include_path":
                    # In <iostream> or "my_header.h" form
                    clean_path = node_text.strip('<>"')
                    parsed_data["imports"].append({
                        "target": clean_path,
                        "alias": None,
                        "type": "system" if node_text.startswith("<") else "local"
                    })

                # --- 2. Macros (#define) ---
                elif capture_name == "macro_name":
                    # Temporarily store macro name (to pair with value capture)
                    self._current_macro_name = node_text
                elif capture_name == "macro_val":
                    parsed_data["macros"].append({
                        "name": getattr(self, "_current_macro_name", "UNKNOWN"),
                        "value": node_text.strip()
                    })

                # --- 3. Classes & Structs ---
                elif capture_name in ["class_name", "struct_name"]:
                    docstring = self._extract_docstring(node.parent)
                    parsed_data["classes"].append({
                        "name": node_text,
                        "type": "class" if capture_name == "class_name" else "struct",
                        "methods": [], # Extract internal functions via nested query if needed
                        "docstring": docstring
                    })

                # --- 4. Functions ---
                elif capture_name == "func_name":
                    # Check whether a function belongs inside a class (simple parent node check)
                    parent = node.parent
                    is_method = False
                    while parent:
                        if parent.type in ["class_specifier", "struct_specifier"]:
                            is_method = True
                            break
                        parent = parent.parent
                    
                    if not is_method:
                        docstring = self._extract_docstring(node.parent.parent)
                        parsed_data["functions"].append({
                            "name": node_text,
                            "docstring": docstring
                        })

        except Exception as e:
            meta["error"] = f"C++ Error during parsing: {str(e)}"

        # Merge parsed data into metadata
        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _extract_docstring(self, node) -> str:
        """
        Extract comments immediately above a specific node (class/function).
        """
        if not node or not node.prev_sibling:
            return ""
        
        comments = []
        current = node.prev_sibling
        # Collect all consecutive comment blocks (// or /* ... */)
        while current and current.type == "comment":
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
            
        return "\n".join(reversed(comments)) if comments else ""

