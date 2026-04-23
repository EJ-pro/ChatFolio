from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class DartParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "dart",
            "imports": [],             # import 'package:flutter/material.dart';
            "classes": [],             # Class info (including Stateless/Stateful flag)
            "is_flutter_script": False,# Whether this is a Flutter UI script
            "has_build_method": False  # Whether a build() method (UI rendering) exists
        }

        # 1. Tree-sitter Query for Dart syntax
        query_source = """
        ;; 1. Capture URI in import statement (e.g., package:flutter)
        (import_directive uri: (string_literal) @import_uri)

        ;; 2. Capture Class declarations, parent class (inheritance), Mixin (with), Interface (implements)
        (class_definition
            name: (identifier) @class_name
            superclass: (superclass (type_identifier) @base_class)?
            interfaces: (interfaces (type_list (type_identifier) @interface_name))?
            mixins: (mixins (type_list (type_identifier) @mixin_name))?
        ) @class_node
        """

        try:
            query = self.language.query(query_source)
            captures = query.captures(self.root_node)

            for node, capture_name in captures:
                node_text = node.text.decode('utf8', errors='ignore')
                
                # --- 1. Imports ---
                if capture_name == "import_uri":
                    # Remove quotes ('package:flutter/material.dart' -> package:flutter/material.dart)
                    uri_text = node_text.strip("'\"")
                    parsed_data["imports"].append(uri_text)
                    
                    # Detect whether this is a Flutter UI component
                    if uri_text.startswith("package:flutter/"):
                        parsed_data["is_flutter_script"] = True

                # --- 2. Class & Widgets (Stateful/Stateless) ---
                elif capture_name == "class_node":
                    class_info = self._process_dart_class(node)
                    parsed_data["classes"].append(class_info)
                    
                    # If at least one class inherits from Flutter Widget, treat as UI file
                    if class_info["widget_type"] != "none":
                        parsed_data["is_flutter_script"] = True
                    
                    # Check whether a build method exists (UI rendering class)
                    if "build" in class_info["methods"]:
                        parsed_data["has_build_method"] = True

        except Exception as e:
            meta["error"] = f"Error during Dart parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta

    def _process_dart_class(self, node) -> Dict[str, Any]:
        """
        Analyze the internal structure of a Dart class to extract Widget type, methods, and comments.
        """
        # 1. Extract class name
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode('utf8', errors='ignore') if name_node else "Unknown"

        # 2. Analyze inheritance (extends) -> classify Flutter Widget type
        base_class_name = ""
        widget_type = "none" # none, stateless, stateful, state, provider
        
        superclass_node = node.child_by_field_name("superclass")
        if superclass_node:
            for child in superclass_node.children:
                if child.type == "type_identifier":
                    base_class_name = child.text.decode('utf8', errors='ignore')
                    break
            
            if base_class_name == "StatelessWidget":
                widget_type = "stateless"
            elif base_class_name == "StatefulWidget":
                widget_type = "stateful"
            elif base_class_name.startswith("State<"): 
                widget_type = "state_logic"
            elif base_class_name == "InheritedWidget":
                widget_type = "inherited_widget"

        # 3. Extract Mixin (with) and Interface (implements)
        mixins = []
        mixins_node = node.child_by_field_name("mixins")
        if mixins_node:
            type_list = mixins_node.child_by_field_name("types")
            if type_list:
                for child in type_list.children:
                    if child.type == "type_identifier":
                        m_name = child.text.decode('utf8', errors='ignore')
                        mixins.append(m_name)
                        if m_name == "ChangeNotifier":
                            widget_type = "provider/notifier"

        interfaces = []
        interfaces_node = node.child_by_field_name("interfaces")
        if interfaces_node:
            type_list = interfaces_node.child_by_field_name("types")
            if type_list:
                for child in type_list.children:
                    if child.type == "type_identifier":
                        interfaces.append(child.text.decode('utf8', errors='ignore'))

        # 4. Traverse methods inside the class
        methods = []
        body_node = node.child_by_field_name("body")
        if body_node:
            for child in body_node.children:
                if child.type == "method_declaration":
                    m_name_node = child.child_by_field_name("name")
                    if m_name_node:
                        methods.append(m_name_node.text.decode('utf8', errors='ignore'))

        # 5. Extract Docstring (//)
        docstring = self._extract_docstring(node)

        return {
            "name": name,
            "inherits": base_class_name,
            "mixins": mixins,
            "interfaces": interfaces,
            "widget_type": widget_type,
            "methods": methods,
            "docstring": docstring
        }

    def _extract_docstring(self, node) -> str:
        """
        Extract Dart official doc comments (/// or //, /* */) by backtracking.
        """
        if not node or not node.prev_sibling:
            return ""
        
        comments = []
        current = node.prev_sibling
        
        while current and current.type == "comment":
            comments.append(current.text.decode('utf8', errors='ignore').strip())
            current = current.prev_sibling
            
        return "\n".join(reversed(comments)) if comments else ""