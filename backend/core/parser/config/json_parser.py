import json
from typing import Dict, Any
from ..tree_sitter_base import BaseTreeSitterParser

class JsonParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "type": "json",
            "dependencies": {},
            "scripts": {},
            "metadata": {}
        }

        try:
            data = json.loads(self.content)
            
            # 1. package.json 특화 분석 (NPM/JS 생태계)
            if "dependencies" in data or "devDependencies" in data or "scripts" in data:
                parsed_data["type"] = "package_json"
                parsed_data["dependencies"] = {
                    "prod": data.get("dependencies", {}),
                    "dev": data.get("devDependencies", {})
                }
                parsed_data["scripts"] = data.get("scripts", {})
                parsed_data["metadata"] = {
                    "name": data.get("name"),
                    "version": data.get("version"),
                    "description": data.get("description")
                }
            
            # 2. 일반 JSON (환경 설정 등)
            else:
                # 너무 큰 데이터는 직렬화 이슈가 있으므로 핵심 키만 추출하거나 요약
                parsed_data["metadata"] = {k: v for k, v in data.items() if isinstance(v, (str, int, bool))}

        except Exception as e:
            meta["error"] = f"JSON 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
