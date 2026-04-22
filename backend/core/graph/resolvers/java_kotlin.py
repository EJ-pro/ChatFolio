from typing import Optional
from .base import BaseResolver

class JavaKotlinResolver(BaseResolver):
    def resolve(self, path: str, import_str: str) -> Optional[str]:
        # 'import com.example.service.MyService;' -> 'com.example.service.MyService'
        src = import_str.replace(";", "").replace("import ", "").strip()

        # 1. 완전한 패키지 경로 매핑 (entity_map 사용)
        if src in self.entity_map:
            return self.entity_map[src]

        # 2. 클래스명만 있는 경우 (import com.example.Service 에서 Service 추출)
        last_segment = src.split(".")[-1]
        if last_segment in self.entity_map:
            return self.entity_map[last_segment]

        # 3. 최후의 수단: 파일명 기반 퍼지 매칭
        if last_segment in self.basename_map:
            return self.basename_map[last_segment]

        return None
