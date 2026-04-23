from typing import Optional
from .base import BaseResolver

class JavaKotlinResolver(BaseResolver):
    def resolve(self, path: str, import_str: str) -> Optional[str]:
        # 'import com.example.service.MyService;' -> 'com.example.service.MyService'
        src = import_str.replace(";", "").replace("import ", "").strip()

        # 1. Full package path mapping (using entity_map)
        if src in self.entity_map:
            return self.entity_map[src]

        # 2. Class name only (extract Service from import com.example.Service)
        last_segment = src.split(".")[-1]
        if last_segment in self.entity_map:
            return self.entity_map[last_segment]

        # 3. Last resort: filename-based fuzzy matching
        if last_segment in self.basename_map:
            return self.basename_map[last_segment]

        return None
