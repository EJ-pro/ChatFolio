import os
from typing import Optional
from .base import BaseResolver

class PythonResolver(BaseResolver):
    def resolve(self, path: str, import_str: str) -> list:
        targets = []
        
        # 1. Handle 'from x import y' form
        if " import " in import_str:
            parts = import_str.split(" import ")
            imp_module = parts[0].replace("from ", "").strip()
            imp_symbols = [s.strip() for s in parts[1].split(",")]
            
            # (1) x.y form is an actual module (file) (e.g., from backend.core.parser import cpp_parser)
            for sym in imp_symbols:
                full_module = f"{imp_module}.{sym}"
                if full_module in self.entity_map:
                    targets.append(self.entity_map[full_module])
                elif sym in self.entity_map:
                    # sym is a class declared inside the file
                    targets.append(self.entity_map[sym])
            
            # (2) x form is a module (e.g., from backend.database.models import User)
            if imp_module in self.entity_map:
                targets.append(self.entity_map[imp_module])
                
        else:
            # 'import os, sys' form
            imp_module_str = import_str.replace("import ", "").strip()
            imp_modules = [m.strip() for m in imp_module_str.split(",")]
            for m in imp_modules:
                if m in self.entity_map:
                    targets.append(self.entity_map[m])
                    
        # 2. Relative path and fuzzy matching
        # If not found via entity_map, split by word and compare against basename_map
        if not targets:
            clean_str = import_str.replace("from ", "").replace("import ", "").replace(",", " ")
            words = clean_str.split()
            for w in words:
                last_segment = w.split(".")[-1]
                if last_segment in self.basename_map:
                    targets.append(self.basename_map[last_segment])

        return list(set(targets))
