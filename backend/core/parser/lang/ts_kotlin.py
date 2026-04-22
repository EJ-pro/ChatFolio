from typing import Dict, Any, List
import re
from ..tree_sitter_base import BaseTreeSitterParser

class KotlinParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        parsed_data = {
            "file_path": meta.get("file_path", ""),
            "language": "kotlin",
            "package": "",
            "imports": [],
            "classes": [],
            "functions": [],
            "is_android_project": False
        }

        try:
            # 1. Package
            pkg_match = re.search(r"package\s+([a-zA-Z0-9_.]+)", self.content)
            if pkg_match:
                parsed_data["package"] = pkg_match.group(1).strip()

            # 2. Imports
            import_matches = re.finditer(r"import\s+([a-zA-Z0-9_.*]+)", self.content)
            for match in import_matches:
                parsed_data["imports"].append(match.group(1).strip())

            # 3. Classes
            class_matches = re.finditer(r"class\s+(\w+)", self.content)
            for match in class_matches:
                parsed_data["classes"].append({
                    "name": match.group(1),
                    "inherits": [],
                    "methods": [],
                    "docstring": ""
                })

            if "android" in self.content.lower() or "androidx" in self.content.lower():
                parsed_data["is_android_project"] = True

        except Exception as e:
            meta["error"] = f"Kotlin 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
