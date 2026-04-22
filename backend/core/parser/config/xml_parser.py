import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class XmlParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "type": "xml",
            "maven_dependencies": [],
            "android_permissions": [],
            "metadata": {}
        }

        try:
            # XML 파싱 (네임스페이스를 무시하기 위해 태그 이름을 정규화할 수 있음)
            root = ET.fromstring(self.content)
            
            # 1. Maven (pom.xml) 분석
            if "project" in root.tag:
                parsed_data["type"] = "maven_pom"
                # namespace 처리
                ns = {'m': root.tag.split('}')[0].strip('{')} if '}' in root.tag else {}
                
                # 의존성 추출 (가장 간단한 버전)
                deps = root.findall(".//m:dependency" if ns else ".//dependency", ns)
                for dep in deps:
                    g_id = dep.find("m:groupId" if ns else "groupId", ns)
                    a_id = dep.find("m:artifactId" if ns else "artifactId", ns)
                    if g_id is not None and a_id is not None:
                        parsed_data["maven_dependencies"].append(f"{g_id.text}:{a_id.text}")

            # 2. Android Manifest 분석
            elif "manifest" in root.tag:
                parsed_data["type"] = "android_manifest"
                parsed_data["metadata"]["package"] = root.get("package")
                
                # 권한(Permission) 추출
                perms = root.findall(".//uses-permission")
                for p in perms:
                    name = p.get("{http://schemas.android.com/apk/res/android}name") or p.get("android:name")
                    if name:
                        parsed_data["android_permissions"].append(name)

        except Exception as e:
            meta["error"] = f"XML 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
