from typing import Dict, Any, List
import re
from ..tree_sitter_base import BaseTreeSitterParser

class JavaParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "java",
            "package": "",
            "imports": [],
            "classes": [],
            "interfaces": [],
            "is_spring_boot": False
        }

        try:
            # 1. Package
            pkg_match = re.search(r"package\s+([a-zA-Z0-9_.]+);", self.content)
            if pkg_match:
                parsed_data["package"] = pkg_match.group(1)

            # 2. Imports
            import_matches = re.finditer(r"import\s+(static\s+)?([a-zA-Z0-9_.*]+);", self.content)
            for match in import_matches:
                parsed_data["imports"].append(match.group(2))

            # 3. Classes
            class_matches = re.finditer(r"class\s+(\w+)", self.content)
            for match in class_matches:
                parsed_data["classes"].append({
                    "name": match.group(1),
                    "inherits": [],
                    "methods": [],
                    "docstring": ""
                })

            if "org.springframework" in self.content:
                parsed_data["is_spring_boot"] = True

        except Exception as e:
            meta["error"] = f"Error during Java parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta