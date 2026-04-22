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
            # 1. TOML 분석 (pyproject.toml 등)
            if self.file_path.endswith('.toml'):
                parsed_data["type"] = "toml"
                if tomllib:
                    data = tomllib.loads(self.content)
                    
                    # Poetry 의존성 추출
                    poetry = data.get("tool", {}).get("poetry", {})
                    if poetry:
                        parsed_data["poetry_dependencies"] = {
                            "main": poetry.get("dependencies", {}),
                            "dev": poetry.get("group", {}).get("dev", {}).get("dependencies", {})
                        }
                        parsed_data["metadata"]["name"] = poetry.get("name")

            # 2. YAML 분석 (Docker, Actions 등)
            else:
                parsed_data["type"] = "yaml"
                data = yaml.safe_load(self.content)
                
                if not data: return meta # 빈 파일

                # Docker Compose 분석
                if "services" in data:
                    parsed_data["docker_services"] = list(data["services"].keys())
                
                # GitHub Actions 분석
                if "jobs" in data or "on" in data:
                    parsed_data["github_actions"] = list(data.get("jobs", {}).keys())

        except Exception as e:
            meta["error"] = f"YAML/TOML 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
