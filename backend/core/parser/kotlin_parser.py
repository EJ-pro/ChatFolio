import re

def parse_kotlin_code(code: str) -> dict:
    try:
        # Package 추출 (kts는 없을 수 있음)
        package_match = re.search(r'^package\s+([\w\.]+)', code, re.MULTILINE)
        package = package_match.group(1) if package_match else "script_or_default"

        # Imports 추출
        imports = re.findall(r'^import\s+([\w\.\*]+)', code, re.MULTILINE)

        # Classes / Interfaces 추출
        classes = []
        class_matches = re.finditer(r'(class|interface|object)\s+(\w+)', code)
        for m in class_matches:
            classes.append({"type": m.group(1), "name": m.group(2)})

        # Functions 추출 (Top-level 포함)
        functions = []
        func_matches = re.finditer(r'fun\s+([\w\.]+)', code)
        for m in func_matches:
            functions.append({"name": m.group(1)})

        return {
            "package": package,
            "imports": imports,
            "classes": classes,
            "functions": functions
        }
    except Exception as e:
        return {"error": str(e)}