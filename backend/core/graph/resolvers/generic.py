from typing import Optional
from .base import BaseResolver

class GenericResolver(BaseResolver):
    def resolve(self, path: str, import_str: str) -> Optional[str]:
        # Simple matching based on filename or last identifier
        # 'import "Something"' or 'require "Something"'
        clean_name = import_str.replace('"', '').replace("'", "").replace("import ", "").replace("require ", "").strip()
        last_segment = clean_name.split(".")[-1].split("/")[-1]
        
        if last_segment in self.basename_map:
            return self.basename_map[last_segment]
            
        return None
