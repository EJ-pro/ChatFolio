import yaml
try:
    import tomllib  # Python 3.11+
except ImportError:
    tomllib = None

from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class YamlTomlParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "type": "yaml_toml",
            "docker_services": [],
            "poetry_dependencies": {},
            "github_actions": [],
            "metadata": {}
        }

        try:
            # 1. Analyze TOML (e.g., pyproject.toml)
            if self.file_path.endswith('.toml'):
                parsed_data["type"] = "toml"
                if tomllib:
                    data = tomllib.loads(self.content)
                    
                    # Extract Poetry dependencies
                    poetry = data.get("tool", {}).get("poetry", {})
                    if poetry:
                        parsed_data["poetry_dependencies"] = {
                            "main": poetry.get("dependencies", {}),
                            "dev": poetry.get("group", {}).get("dev", {}).get("dependencies", {})
                        }
                        parsed_data["metadata"]["name"] = poetry.get("name")

            # 2. Analyze YAML (Docker, Actions, etc.)
            else:
                parsed_data["type"] = "yaml"
                data = yaml.safe_load(self.content)
                
                if not data: return meta # Empty file

                # Analyze Docker Compose
                if "services" in data:
                    parsed_data["docker_services"] = list(data["services"].keys())
                
                # Analyze GitHub Actions
                if "jobs" in data or "on" in data:
                    parsed_data["github_actions"] = list(data.get("jobs", {}).keys())

        except Exception as e:
            meta["error"] = f"YAML/TOML Error during parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
