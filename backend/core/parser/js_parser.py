import re

def parse_js_ts_code(code: str) -> dict:
    """
    JavaScript/TypeScript 코드를 정규표현식으로 분석하여 메타데이터를 추출합니다.
    """
    lines = code.split('\n')
    line_count = len(lines)
    
    try:
        imports = []
        classes = []
        functions = []
        ts_elements = [] # interfaces, types
        
        # 1. 첫 번째 주석 블록 추출
        comment_match = re.search(r'/\*\*[\s\S]*?\*/', code) or re.search(r'//.*', code)
        summary = comment_match.group(0).strip() if comment_match else ""
        
        # 2. 라인 단위로 순회
        for i, line in enumerate(lines):
            line_num = i + 1
            line = line.strip()
            
            # Import 매칭 (import ... from '...' or require('...'))
            imp_match = re.search(r'import\s+.*from\s+[\'"](.+)[\'"]', line) or re.search(r'require\([\'"](.+)[\'"]\)', line)
            if imp_match:
                imports.append(imp_match.group(1))
                
            # Class 매칭
            cls_match = re.search(r'class\s+(\w+)', line)
            if cls_match:
                classes.append({
                    "name": cls_match.group(1), 
                    "line": line_num
                })
                
            # Function 매칭 (function name() or const name = () =>)
            func_match = re.search(r'function\s+(\w+)', line) or re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\(.*\)|.*?)\s*=>', line)
            if func_match:
                functions.append({
                    "name": func_match.group(1), 
                    "line": line_num
                })

            # TS 특정 요소 (interface, type)
            ts_match = re.search(r'(interface|type)\s+(\w+)', line)
            if ts_match:
                ts_elements.append({
                    "type": ts_match.group(1),
                    "name": ts_match.group(2),
                    "line": line_num
                })

        keywords = list(set(
            [c["name"] for c in classes] + 
            [f["name"] for f in functions] + 
            [t["name"] for t in ts_elements]
        ))

        return {
            "line_count": line_count,
            "keywords": keywords,
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "metadata_json": {
                "imports": imports,
                "classes": classes,
                "functions": functions,
                "ts_elements": ts_elements,
                "summary": summary[:500]
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "line_count": line_count,
            "keywords": [],
            "metadata_json": {}
        }
