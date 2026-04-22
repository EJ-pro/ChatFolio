import os
from typing import Optional
from .base import BaseResolver

class JSResolver(BaseResolver):
    def resolve(self, path: str, import_str: str) -> Optional[str]:
        # Tree-sitter 파서에서 이미 따옴표는 제거된 상태라고 가정 (src = './utils')
        src = import_str.strip()
        current_dir = os.path.dirname(path)

        # 1. 상대 경로 해결 (./, ../)
        if src.startswith("."):
            abs_candidate = os.path.normpath(os.path.join(current_dir, src)).replace("\\", "/")
            
            # 확장자 및 index 파일 시도 (JS/TS 관례)
            for ext in ['', '.js', '.ts', '.jsx', '.tsx']:
                # 파일 직접 대조
                test_path = abs_candidate + ext
                if test_path in self.full_path_map:
                    return self.full_path_map[test_path]
                
                # 폴더 내 index 파일 대조
                if not ext: continue # index는 확장자가 있어야 함
                test_index = os.path.join(abs_candidate, f"index{ext}").replace("\\", "/")
                if test_index in self.full_path_map:
                    return self.full_path_map[test_index]

        # 2. 절대 경로 또는 모듈명 매핑
        if src in self.entity_map:
            return self.entity_map[src]

        # 3. 최후의 수단: 파일명 기반 퍼지 매칭
        # 'import { User } from "src/models"' -> 'models'
        last_part = src.split("/")[-1]
        if last_part in self.basename_map:
            return self.basename_map[last_part]

        return None
