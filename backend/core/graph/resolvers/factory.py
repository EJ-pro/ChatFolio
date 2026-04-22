from typing import Dict, Any, Optional
from .base import BaseResolver
from .python import PythonResolver
from .javascript import JSResolver
from .java_kotlin import JavaKotlinResolver
from .generic import GenericResolver

class ResolverFactory:
    @staticmethod
    def get_resolver(language: str, full_path_map: dict, basename_map: dict, entity_map: dict) -> BaseResolver:
        lang = language.lower()
        
        if lang == "python":
            return PythonResolver(full_path_map, basename_map, entity_map)
        elif lang in ["javascript", "typescript", "jsx", "tsx"]:
            return JSResolver(full_path_map, basename_map, entity_map)
        elif lang in ["java", "kotlin"]:
            return JavaKotlinResolver(full_path_map, basename_map, entity_map)
        
        # 기본 리졸버 (기타 언어용)
        return GenericResolver(full_path_map, basename_map, entity_map) 
