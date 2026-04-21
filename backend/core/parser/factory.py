from .kotlin_parser import parse_kotlin_code, generic_extract_metadata
from .ast_parser import parse_python_code
from .java_parser import parse_java_code
from .js_parser import parse_js_ts_code
from .cpp_parser import parse_cpp_code

def get_parser_result(path: str, content: str) -> dict:
    """
    파일 확장자에 따라 적절한 파서를 호출하여 메타데이터를 반환합니다.
    """
    ext = path.split('.')[-1].lower() if '.' in path else ''
    
    if ext in ['kt', 'kts']:
        return parse_kotlin_code(content)
    elif ext == 'py':
        return parse_python_code(content)
    elif ext == 'java':
        return parse_java_code(content)
    elif ext in ['js', 'jsx', 'ts', 'tsx']:
        return parse_js_ts_code(content)
    elif ext in ['cpp', 'c', 'h', 'hpp', 'cc']:
        return parse_cpp_code(content)
    else:
        # 기타 파일들은 기본 메타데이터 추출만 수행
        return generic_extract_metadata(path, content)
