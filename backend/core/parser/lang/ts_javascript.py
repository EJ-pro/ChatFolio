from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser
import re

class JavaScriptParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "javascript",
            "imports": [],
            "exports": [],
            "functions": [],
            "classes": [],
            "is_react_component": False
        }

        try:
            # 1. Imports extracting via Regex (import X from 'Y', require('Y'), import {X} from "Y")
            import_patterns = [
                r"import\s+.*?\s+from\s+['\"](.*?)['\"]",
                r"import\s+['\"](.*?)['\"]",
                r"require\(['\"](.*?)['\"]\)"
            ]
            
            for pattern in import_patterns:
                matches = re.finditer(pattern, self.content, re.MULTILINE)
                for match in matches:
                    src = match.group(1).strip()
                    if src not in parsed_data["imports"]:
                        parsed_data["imports"].append(src)

            # 2. JSX/React detection
            if re.search(r"<\w+[^>]*>.*?</\w+>", self.content, re.DOTALL) or re.search(r"<\w+[^>]*/>", self.content):
                parsed_data["is_react_component"] = True
            
            if "react" in self.content.lower() and "export default function" in self.content:
                parsed_data["is_react_component"] = True

            # 3. Simple class names
            class_matches = re.finditer(r"class\s+(\w+)", self.content)
            for match in class_matches:
                parsed_data["classes"].append({
                    "name": match.group(1),
                    "inherits": [],
                    "methods": [],
                    "docstring": ""
                })

        except Exception as e:
            meta["error"] = f"JS 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta