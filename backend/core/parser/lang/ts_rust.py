from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class RustParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "language": "rust",
            "uses": [],                # use std::collections::HashMap;
            "mods": [],                # mod my_module;
            "structs": [],             # struct MyStruct { ... }
            "enums": [],               # enum MyEnum { ... }
            "traits": [],              # trait MyTrait { ... }
            "impls": [],               # impl MyTrait for MyStruct { ... }
            "functions": []            # global/mod level functions
        }

        # 1. Tree-sitter Query for Rust syntax
        query_source = """
        ;; 1. Extract Use (dependencies)
        (use_declaration argument: (_) @use_path)

        ;; 2. Extract Mod definitions
        (mod_item name: (identifier) @mod_name) @mod_node

        ;; 3. Extract Struct, Enum, Trait declarations
        (struct_item name: (type_identifier) @struct_name) @struct_node
        (enum_item name: (type_identifier) @enum_name) @enum_node
        (trait_item name: (type_identifier) @trait_name) @trait_node

        ;; 4. Extract Impl blocks (including Trait implementation flag)
        (impl_item
            trait: (type_identifier)? @impl_trait
            type: (type_identifier) @impl_struct
        ) @impl_node

        ;; 5. Extract Functions
        (function_item name: (identifier) @func_name) @func_node
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')

                # --- 1. Uses & Mods ---
                if capture_name == "use_path":
                    parsed_data["uses"].append(node_text)
                elif capture_name == "mod_name":
                    parsed_data["mods"].append({
                        "name": node_text,
                        "docstring": self._extract_docstring(node.parent)
                    })

                # --- 2. Types (Struct, Enum, Trait) ---
                elif capture_name in ["struct_name", "enum_name", "trait_name"]:
                    category = capture_name.split('_')[0] + "s"
                    parsed_data[category].append(self._process_rust_node(node.parent, category[:-1]))

                # --- 3. Impls ---
                elif capture_name == "impl_struct":
                    # If trait_name exists: 'Trait for Struct'; otherwise: direct implementation for 'Struct'
                    trait_node = None
                    for sibling in node.parent.children:
                        if sibling.type == "type_identifier" and sibling != node:
                            trait_node = sibling
                            break
                    
                    parsed_data["impls"].append({
                        "struct": node_text,
                        "trait": trait_node.text.decode('utf8', errors='ignore') if trait_node else None,
                        "methods": self._extract_impl_methods(node.parent)
                    })

                # --- 4. Global Functions ---
                elif capture_name == "func_name":
                    if self._is_global_scope(node):
                        parsed_data["functions"].append({
                            "name": node_text,
                            "docstring": self._extract_docstring(node.parent)
                        })

        except Exception as e:
            meta["error"] = f"Error during Rust parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_rust_node(self, node, node_type: str) -> Dict[str, Any]:
        """Analyze the internals of a Rust struct, enum, or trait."""
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"

        # For Traits, internal method signatures can be extracted
        methods = []
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type in ["function_item", "function_signature_item"]:
                    m_name_node = child.child_by_field_name("name")
                    if m_name_node:
                        methods.append(m_name_node.text.decode('utf8', errors='ignore'))

        return {
            "name": name,
            "type": node_type,
            "methods": methods,
            "docstring": self._extract_docstring(node)
        }

    def _extract_impl_methods(self, impl_node) -> List[str]:
        """Extract method names defined inside an impl block."""
        methods = []
        body = impl_node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "function_item":
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        methods.append(name_node.text.decode('utf8', errors='ignore'))
        return methods

    def _is_global_scope(self, node) -> bool:
        """Check whether a function is at the module/global level, not inside an impl or trait."""
        curr = node.parent
        while curr:
            if curr.type in ["impl_item", "trait_item"]:
                return False
            curr = curr.parent
        return True

    def _extract_docstring(self, node) -> str:
        """Extract Rust doc comments (/// or //!)."""
        if not node or not node.prev_sibling:
            return ""
        comments = []
        current = node.prev_sibling
        while current and current.type in ["line_comment", "block_comment"]:
            text = current.text.decode('utf8', errors='ignore').strip()
            # Collect Rust-specific /// or //! comments (can be filtered later)
            comments.append(text)
            current = current.prev_sibling
        return "\n".join(reversed(comments)) if comments else ""
