import re
from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class GradleParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "type": "gradle",
            "dependencies": [],         # implementation, api 등 라이브러리
            "plugins": [],              # apply plugin, plugins { ... }
            "metadata": {}
        }

        try:
            # 1. 의존성 추출 (정규식 기반)
            # 패턴: implementation 'group:name:version' 또는 implementation("...")
            dep_pattern = r"(?:implementation|api|testImplementation|runtimeOnly|compileOnly)\s*\(?[\'\"]([^\"\'\)]+)[\'\"]"
            deps = re.findall(dep_pattern, self.content)
            parsed_data["dependencies"] = list(set(deps)) # 중복 제거

            # 2. 플러그인 추출
            # 패턴: id 'com.android.application' 또는 apply plugin: '...'
            plugin_id_pattern = r"id\s*[\'\"]([^\"\'\s]+)[\'\"]"
            plugin_apply_pattern = r"apply\s+plugin:\s*[\'\"]([^\"\'\s]+)[\'\"]"
            
            plugins = re.findall(plugin_id_pattern, self.content)
            plugins.extend(re.findall(plugin_apply_pattern, self.content))
            parsed_data["plugins"] = list(set(plugins))

            # 3. 주요 설정 감지
            if "com.android.application" in parsed_data["plugins"] or "com.android.library" in parsed_data["plugins"]:
                parsed_data["metadata"]["is_android"] = True
            if "org.springframework.boot" in parsed_data["plugins"]:
                parsed_data["metadata"]["is_spring_boot"] = True

        except Exception as e:
            meta["error"] = f"Gradle 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
