from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class BaseResolver(ABC):
    def __init__(self, full_path_map: Dict[str, str], basename_map: Dict[str, str], entity_map: Dict[str, str]):
        self.full_path_map = full_path_map
        self.basename_map = basename_map
        self.entity_map = entity_map

    @abstractmethod
    def resolve(self, path: str, import_str: str) -> Optional[str]:
        """
        Resolve an import string to an actual file path.
        :param path: Full path of the current source file
        :param import_str: Raw parsed import string or refined identifier
        :return: Full path of the matched file, or None
        """
        pass
