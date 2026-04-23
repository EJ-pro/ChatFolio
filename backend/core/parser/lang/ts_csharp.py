from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class CSharpParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "csharp",
            "usings": [],              # e.g., using System.Linq;
            "namespaces": [],          # namespace definitions
            "classes": [],             # classes (including inheritance and methods)
            "interfaces": [],          # interface declarations
            "linq_query_count": 0,     # Number of LINQ usages
            "is_unity_script": False   # Flag for Unity environment file
        }

        # 1. Tree-sitter Query for top-level structure and LINQ identification
        query_source = """
        ;; Capture name area of using statement
        (using_directive name: (_) @using_name)

        ;; Capture class, interface, and namespace declarations
        (namespace_declaration name: (_) @namespace_name)
        (class_declaration) @class_node
        (interface_declaration) @interface_node

        ;; Capture LINQ query expressions (from ... select ...)
        (query_expression) @linq_expr
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')

                # --- 1. Namespaces & Usings ---
                if capture_name == "using_name":
                    parsed_data["usings"].append(node_text)
                    if "UnityEngine" in node_text:
                        parsed_data["is_unity_script"] = True
                
                elif capture_name == "namespace_name":
                    parsed_data["namespaces"].append(node_text)

                # --- 2. Class & Inheritance ---
                elif capture_name == "class_node":
                    class_info = self._process_class_or_interface(node, node_type="class")
                    parsed_data["classes"].append(class_info)
                    
                    # Mark as Unity script when MonoBehaviour inheritance is detected
                    if "MonoBehaviour" in class_info["inherits"]:
                        parsed_data["is_unity_script"] = True

                # --- 3. Interfaces ---
                elif capture_name == "interface_node":
                    interface_info = self._process_class_or_interface(node, node_type="interface")
                    parsed_data["interfaces"].append(interface_info)

                # --- 4. LINQ Queries ---
                elif capture_name == "linq_expr":
                    parsed_data["linq_query_count"] += 1

        except Exception as e:
            meta["error"] = f"Error during C# parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_class_or_interface(self, node, node_type: str) -> Dict[str, Any]:
        """
        Extract inheritance relationships and methods hierarchically from a class or interface node.
        This prevents nested classes or out-of-scope functions from mixing in.
        """
        # 1. Extract name
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"

        # 2. Extract inheritance/implementation (bases)
        inherits = []
        bases_node = node.child_by_field_name("bases")
        if bases_node:
            # Extract type identifiers inside base_list (e.g., MonoBehaviour, IDisposable)
            for child in bases_node.children:
                # Exclude ':' and extract actual type names only
                if child.type not in [":", ","]:
                    inherits.append(child.text.decode('utf8', errors='ignore').strip())

        # 3. Extract internal methods (traverse body)
        methods = []
        body_node = node.child_by_field_name("body")
        if body_node:
            for child in body_node.children:
                # C# has constructor_declaration in addition to method_declaration
                if child.type in ["method_declaration", "constructor_declaration"]:
                    m_name_node = child.child_by_field_name("name")
                    if m_name_node:
                        methods.append(m_name_node.text.decode('utf8', errors='ignore'))

        # 4. Extract Docstring (XML comment ///)
        docstring = self._extract_docstring(node)

        return {
            "name": name,
            "inherits": inherits,
            "methods": methods,
            "docstring": docstring
        }

    def _extract_docstring(self, node) -> str:
        """
        Extract traditional C# XML comments (///) or regular comments (//, /* */).
        """
        if not node or not node.prev_sibling:
            return ""
        
        comments = []
        current = node.prev_sibling
        
        while current and current.type == "comment":
            # For C# XML comments in '/// <summary>' format, tags can optionally be cleaned.
            text = current.text.decode('utf8', errors='ignore').strip()
            comments.append(text)
            current = current.prev_sibling
            
        return "\n".join(reversed(comments)) if comments else ""