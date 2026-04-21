import re

def parse_kotlin_code(code: str) -> dict:
    """
    코틀린 코드를 정규표현식으로 분석하여 메타데이터와 라인 번호를 추출합니다.
    """
    lines = code.split('\n')
    line_count = len(lines)
    
    try:
        # 1. Package 추출
        package_match = re.search(r'^package\s+([\w\.]+)', code, re.MULTILINE)
        package = package_match.group(1) if package_match else "script_or_default"

        imports = []
        classes = []
        functions = []
        annotations = []
        
        # 2. 첫 번째 주석 블록 (KDoc/Comment) 추출
        comment_match = re.search(r'/\*\*[\s\S]*?\*/', code) or re.search(r'//.*', code)
        summary = comment_match.group(0).strip() if comment_match else ""
        
        # 3. 라인 단위로 순회하며 정보 추출
        for i, line in enumerate(lines):
            line_num = i + 1
            line = line.strip()
            
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

            # Annotation 매칭 (@Annotation)
            anno_match = re.search(r'@(\w+)', line)
            if anno_match:
                annotations.append(anno_match.group(1))

        # 키워드 조합 (클래스명, 함수명, 주요 어노테이션)
        keywords = list(set([c["name"] for c in classes] + [f["name"] for f in functions] + annotations))

        return {
            "package": package,
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "annotations": list(set(annotations)),
            "summary_comment": summary[:500], # 너무 길면 자름
            "line_count": line_count,
            "keywords": keywords,
            "raw_lines": lines
        }
    except Exception as e:
        return {
            "error": str(e), 
            "line_count": line_count,
            "raw_lines": lines
        }

def generic_extract_metadata(path: str, content: str) -> dict:
    """
    코틀린 외의 파일들에 대해 기본적인 메타데이터(라인수, 키워드 일부)를 추출합니다.
    """
    lines = content.split('\n')
    line_count = len(lines)
    
    # 확장자별 키워드 추출 시도
    keywords = []
    if path.endswith(('.py', '.js', '.ts', '.java')):
        # 함수나 클래스 정의 키워드 주변 단어 추출
        matches = re.findall(r'(?:def|class|function|const|let|var)\s+(\w+)', content)
        keywords.extend(matches)
    
    # 셰릴락 방식의 간단한 빈도 분석이나 파일명 기반 키워드 추가 가능
    file_name = path.split('/')[-1].split('.')[0]
    keywords.append(file_name)

    return {
        "line_count": line_count,
        "keywords": list(set(keywords)),
        "file_size": len(content.encode('utf-8'))
    }