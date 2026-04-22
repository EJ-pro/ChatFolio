import re
from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class SqlParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "type": "sql",
            "tables": [],              # CREATE TABLE 대상
            "operations": {             # 주요 명령 빈도
                "select": 0,
                "insert": 0,
                "update": 0,
                "delete": 0,
                "create": 0
            }
        }

        try:
            # 1. 테이블 생성문 추출 (CREATE TABLE `name`)
            # 패턴: CREATE TABLE [IF NOT EXISTS] 'table_name'
            table_pattern = r"(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[\"`'\[])?([a-zA-Z0-9_]+)(?:[\"`'\]])?"
            tables = re.findall(table_pattern, self.content)
            parsed_data["tables"] = list(set(tables))

            # 2. 주요 연산 키워드 빈도 분석
            content_lower = self.content.lower()
            parsed_data["operations"]["select"] = content_lower.count("select ")
            parsed_data["operations"]["insert"] = content_lower.count("insert into")
            parsed_data["operations"]["update"] = content_lower.count("update ")
            parsed_data["operations"]["delete"] = content_lower.count("delete from")
            parsed_data["operations"]["create"] = content_lower.count("create ")

        except Exception as e:
            meta["error"] = f"SQL 파싱 중 오류 발생: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
