from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseTreeSitterParser(ABC):
    """
    모든 Tree-sitter 기반 파서와 특수 설정 파서가 상속받는 기본 클래스.
    공통된 메타데이터 형식을 정의하고, 추상 메서드 구현을 강제합니다.
    """
    
    def __init__(self, content: str, file_path: str = ""):
        self.content = content
        self.file_path = file_path
        self.line_count = len(content.splitlines()) if content else 0
        self.language = None
        self.root_node = None
        
    def extract_base_metadata(self) -> Dict[str, Any]:
        """추출된 공통 메타데이터 기본 형태 반환"""
        return {
            "file_path": self.file_path,
            "line_count": self.line_count,
            "keywords": [],
            "metadata_json": {}
        }
        
    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """
        각 언어별 파서가 반드시 구현해야 하는 핵심 메서드.
        AST 구문을 분석한 뒤 완성된 메타데이터 사전을 반환해야 합니다.
        """
        pass
