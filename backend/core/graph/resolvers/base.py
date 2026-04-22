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
        인포트 문자열을 실제 파일 경로로 변환합니다.
        :param path: 현재 소스 파일의 전체 경로
        :param import_str: 파싱된 임포트 원문 또는 정제된 식별자
        :return: 매칭되는 파일의 전체 경로 또는 None
        """
        pass
