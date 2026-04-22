import os
from typing import Optional
from .base import BaseResolver

class PythonResolver(BaseResolver):
    def resolve(self, path: str, import_str: str) -> list:
        targets = []
        
        # 1. 'from x import y' 형태 처리
        if " import " in import_str:
            parts = import_str.split(" import ")
            imp_module = parts[0].replace("from ", "").strip()
            imp_symbols = [s.strip() for s in parts[1].split(",")]
            
            # (1) x.y 형태가 실제 모듈(파일)인 경우 (from backend.core.parser import cpp_parser)
            for sym in imp_symbols:
                full_module = f"{imp_module}.{sym}"
                if full_module in self.entity_map:
                    targets.append(self.entity_map[full_module])
                elif sym in self.entity_map:
                    # sym이 파일 내부에 선언된 클래스인 경우
                    targets.append(self.entity_map[sym])
            
            # (2) x 형태가 모듈인 경우 (from backend.database.models import User)
            if imp_module in self.entity_map:
                targets.append(self.entity_map[imp_module])
                
        else:
            # 'import os, sys' 형태
            imp_module_str = import_str.replace("import ", "").strip()
            imp_modules = [m.strip() for m in imp_module_str.split(",")]
            for m in imp_modules:
                if m in self.entity_map:
                    targets.append(self.entity_map[m])
                    
        # 2. 상대 경로 및 퍼지 매칭
        # entity_map으로 찾지 못한 경우 단어 단위로 분리하여 basename_map 대조
        if not targets:
            clean_str = import_str.replace("from ", "").replace("import ", "").replace(",", " ")
            words = clean_str.split()
            for w in words:
                last_segment = w.split(".")[-1]
                if last_segment in self.basename_map:
                    targets.append(self.basename_map[last_segment])

        return list(set(targets))
