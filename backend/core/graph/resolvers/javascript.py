import os
from typing import Optional
from .base import BaseResolver

class JSResolver(BaseResolver):
    def resolve(self, path: str, import_str: str) -> Optional[str]:
        # Assume quotes are already stripped by the Tree-sitter parser (e.g., src = './utils')
        src = import_str.strip()
        current_dir = os.path.dirname(path)

        # 1. Resolve relative paths (./, ../)
        if src.startswith("."):
            abs_candidate = os.path.normpath(os.path.join(current_dir, src)).replace("\\", "/")
            
            # Try extensions and index files (JS/TS convention)
            for ext in ['', '.js', '.ts', '.jsx', '.tsx']:
                # Direct file comparison
                test_path = abs_candidate + ext
                if test_path in self.full_path_map:
                    return self.full_path_map[test_path]
                
                # Compare index files within the folder
                if not ext: continue # index file must have an extension
                test_index = os.path.join(abs_candidate, f"index{ext}").replace("\\", "/")
                if test_index in self.full_path_map:
                    return self.full_path_map[test_index]

        # 2. Absolute path or module name mapping
        if src in self.entity_map:
            return self.entity_map[src]

        # 3. Last resort: filename-based fuzzy matching
        # 'import { User } from "src/models"' -> 'models'
        last_part = src.split("/")[-1]
        if last_part in self.basename_map:
            return self.basename_map[last_part]

        return None
