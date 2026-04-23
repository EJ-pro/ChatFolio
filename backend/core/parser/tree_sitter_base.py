from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseTreeSitterParser(ABC):
    """
    Base class inherited by all Tree-sitter-based parsers and special config parsers.
    Defines the common metadata format and enforces implementation of abstract methods.
    """
    
    def __init__(self, content: str, file_path: str = ""):
        self.content = content
        self.file_path = file_path
        self.line_count = len(content.splitlines()) if content else 0
        self.language = None
        self.root_node = None
        
    def extract_base_metadata(self) -> Dict[str, Any]:
        """Return the default common metadata structure."""
        return {
            "file_path": self.file_path,
            "line_count": self.line_count,
            "keywords": [],
            "metadata_json": {}
        }
        
    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """
        Core method that must be implemented by each language-specific parser.
        Must analyze the AST and return a completed metadata dictionary.
        """
        pass
