import re
from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class GradleParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "type": "gradle",
            "dependencies": [],         # libraries such as implementation, api, etc.
            "plugins": [],              # apply plugin, plugins { ... }
            "metadata": {}
        }

        try:
            # 1. Extract dependencies (regex-based)
            # Pattern: implementation 'group:name:version' or implementation("...")
            dep_pattern = r"(?:implementation|api|testImplementation|runtimeOnly|compileOnly)\s*\(?[\'\"]([^\"\'\)]+)[\'\"]"
            deps = re.findall(dep_pattern, self.content)
            parsed_data["dependencies"] = list(set(deps)) # Remove duplicates

            # 2. Extract plugins
            # Pattern: id 'com.android.application' or apply plugin: '...'
            plugin_id_pattern = r"id\s*[\'\"]([^\"\'\s]+)[\'\"]"
            plugin_apply_pattern = r"apply\s+plugin:\s*[\'\"]([^\"\'\s]+)[\'\"]"
            
            plugins = re.findall(plugin_id_pattern, self.content)
            plugins.extend(re.findall(plugin_apply_pattern, self.content))
            parsed_data["plugins"] = list(set(plugins))

            # 3. Detect key configuration
            if "com.android.application" in parsed_data["plugins"] or "com.android.library" in parsed_data["plugins"]:
                parsed_data["metadata"]["is_android"] = True
            if "org.springframework.boot" in parsed_data["plugins"]:
                parsed_data["metadata"]["is_spring_boot"] = True

        except Exception as e:
            meta["error"] = f"Gradle Error during parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
