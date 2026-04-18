import re

def parse_kotlin_code(code: str) -> dict:
    """
    코틀린 코드를 정규표현식으로 분석하여 메타데이터와 라인 번호를 추출합니다.
    """
    lines = code.split('\n')
    
    try:
        # 1. Package 추출
        package_match = re.search(r'^package\s+([\w\.]+)', code, re.MULTILINE)
        package = package_match.group(1) if package_match else "script_or_default"

        imports = []
        classes = []
        functions = []
        
        # 2. 라인 단위로 순회하며 Import, Class, Function 및 라인 번호 추출
        for i, line in enumerate(lines):
            line_num = i + 1 # 라인 번호는 1부터 시작
            
            # Import 매칭
            imp_match = re.search(r'^import\s+([\w\.\*]+)', line)
            if imp_match:
                imports.append(imp_match.group(1))
                
            # Class/Interface/Object 매칭
            cls_match = re.search(r'(class|interface|object)\s+(\w+)', line)
            if cls_match:
                classes.append({
                    "type": cls_match.group(1), 
                    "name": cls_match.group(2), 
                    "line": line_num
                })
                
            # Function 매칭 (fun 이름)
            func_match = re.search(r'fun\s+([\w\.]+)', line)
            if func_match:
                functions.append({
                    "name": func_match.group(1), 
                    "line": line_num
                })

        return {
            "package": package,
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "raw_lines": lines # 향후 코드 원본 매칭을 위해 저장
        }
    except Exception as e:
        return {"error": str(e), "raw_lines": lines}