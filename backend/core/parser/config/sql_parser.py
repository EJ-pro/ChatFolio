import re
from typing import Dict, Any, List
from ..tree_sitter_base import BaseTreeSitterParser

class SqlParser(BaseTreeSitterParser):
    def parse(self) -> Dict[str, Any]:
        meta = self.extract_base_metadata()
        
        parsed_data = {
            "file_path": self.file_path,
            "type": "sql",
            "tables": [],              # CREATE TABLE targets
            "operations": {             # Frequency of key commands
                "select": 0,
                "insert": 0,
                "update": 0,
                "delete": 0,
                "create": 0
            }
        }

        try:
            # 1. Extract table creation statements (CREATE TABLE `name`)
            # Pattern: CREATE TABLE [IF NOT EXISTS] 'table_name'
            table_pattern = r"(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[\"`'\[])?([a-zA-Z0-9_]+)(?:[\"`'\]])?"
            tables = re.findall(table_pattern, self.content)
            parsed_data["tables"] = list(set(tables))

            # 2. Analyze frequency of key operation keywords
            content_lower = self.content.lower()
            parsed_data["operations"]["select"] = content_lower.count("select ")
            parsed_data["operations"]["insert"] = content_lower.count("insert into")
            parsed_data["operations"]["update"] = content_lower.count("update ")
            parsed_data["operations"]["delete"] = content_lower.count("delete from")
            parsed_data["operations"]["create"] = content_lower.count("create ")

        except Exception as e:
            meta["error"] = f"SQL Error during parsing: {str(e)}"

        meta["metadata_json"]["parsed"] = parsed_data
        return meta
