import re

def parse_cpp_code(code: str) -> dict:
    """
    C/C++ 코드를 정규표현식으로 분석하여 메타데이터를 추출합니다.
    """
    lines = code.split('\n')
    line_count = len(lines)
    
    try:
        includes = []
        classes = [] # includes structs
        functions = []
        namespaces = []
        
        # 1. 첫 번째 주석 블록 추출
        comment_match = re.search(r'/\*[\s\S]*?\*/', code) or re.search(r'//.*', code)
        summary = comment_match.group(0).strip() if comment_match else ""
        
        # 2. 라인 단위로 순회
        for i, line in enumerate(lines):
            line_num = i + 1
            line = line.strip()
            
            # Include 매칭 (#include <...> or #include "...")
            inc_match = re.search(r'#include\s+[<"](.+)[>"]', line)
            if inc_match:
                includes.append(inc_match.group(1))
                
            # Class/Struct 매칭
            cls_match = re.search(r'(class|struct)\s+(\w+)', line)
            if cls_match:
                classes.append({
                    "type": cls_match.group(1),
                    "name": cls_match.group(2), 
                    "line": line_num
                })
                
            # Namespace 매칭
            ns_match = re.search(r'namespace\s+(\w+)', line)
            if ns_match:
                namespaces.append(ns_match.group(1))
                
            # Function 매칭 (int func(args) {)
            # C++은 리턴 타입이 다양하므로 포괄적인 패턴 사용
            func_match = re.search(r'(?:[\w:]+)\s+(\w+)\s*\([^;]*\)\s*\{', line)
            if func_match:
                name = func_match.group(1)
                if name not in ['if', 'while', 'for', 'switch', 'catch']:
                    functions.append({
                        "name": name, 
                        "line": line_num
                    })

        keywords = list(set(
            [c["name"] for c in classes] + 
            [f["name"] for f in functions] + 
            namespaces
        ))

        return {
            "line_count": line_count,
            "keywords": keywords,
            "imports": includes, # standard field name for imports/includes
            "classes": classes,
            "functions": functions,
            "metadata_json": {
                "includes": includes,
                "classes": classes,
                "functions": functions,
                "namespaces": namespaces,
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
