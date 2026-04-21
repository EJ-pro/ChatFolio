import re

def parse_java_code(code: str) -> dict:
    """
    Java 코드를 정규표현식으로 분석하여 메타데이터를 추출합니다.
    """
    lines = code.split('\n')
    line_count = len(lines)
    
    try:
        # 1. Package 추출
        package_match = re.search(r'^package\s+([\w\.]+)', code, re.MULTILINE)
        package = package_match.group(1) if package_match else ""

        imports = []
        classes = []
        functions = []
        annotations = []
        
        # 2. 첫 번째 주석 블록 추출
        comment_match = re.search(r'/\*\*[\s\S]*?\*/', code) or re.search(r'//.*', code)
        summary = comment_match.group(0).strip() if comment_match else ""
        
        # 3. 라인 단위로 순회
        for i, line in enumerate(lines):
            line_num = i + 1
            line = line.strip()
            
            # Import 매칭
            imp_match = re.search(r'^import\s+([\w\.\*]+)', line)
            if imp_match:
                imports.append(imp_match.group(1))
                
            # Class/Interface/Enum 매칭
            cls_match = re.search(r'(class|interface|enum)\s+(\w+)', line)
            if cls_match:
                classes.append({
                    "type": cls_match.group(1), 
                    "name": cls_match.group(2), 
                    "line": line_num
                })
                
            # Method 매칭 (간단한 형태: public void methodName)
            # Java 메서드는 리턴 타입이 필수이므로 Kotlin보다 복잡할 수 있음
            # PoC 수준에서는 접근 제어자 + 리턴타입 + 이름 패턴 사용
            method_match = re.search(r'(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\(', line)
            if method_match:
                name = method_match.group(2)
                if name not in ['if', 'for', 'while', 'switch', 'synchronized', 'catch']:
                    functions.append({
                        "name": name, 
                        "line": line_num
                    })

            # Annotation 매칭
            anno_match = re.search(r'@(\w+)', line)
            if anno_match:
                annotations.append(anno_match.group(1))

        keywords = list(set([c["name"] for c in classes] + [f["name"] for f in functions] + annotations))

        return {
            "line_count": line_count,
            "keywords": keywords,
            "package": package,
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "metadata_json": {
                "package": package,
                "imports": imports,
                "classes": classes,
                "functions": functions,
                "annotations": list(set(annotations)),
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
