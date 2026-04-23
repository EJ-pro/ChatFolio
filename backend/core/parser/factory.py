# New Tree-sitter Language Parsers
from .lang.ts_javascript import JavaScriptParser
from .lang.ts_python import PythonParser
from .lang.ts_java import JavaParser
from .lang.ts_kotlin import KotlinParser
from .lang.ts_go import GoParser
from .lang.ts_csharp import CSharpParser
from .lang.ts_dart import DartParser
from .lang.ts_cpp import CppParser
from .lang.ts_rust import RustParser
from .lang.ts_swift import SwiftParser
from .lang.ts_ruby import RubyParser
from .lang.ts_php import PhpParser

# New Tree-sitter Config Parsers
from .config.json_parser import JsonParser
from .config.xml_parser import XmlParser
from .config.yaml_parser import YamlTomlParser
from .config.gradle_parser import GradleParser
from .config.sql_parser import SqlParser

def generic_extract_metadata(path: str, content: str) -> dict:
    """Default fallback parser for files with unsupported extensions."""
    lines = content.split('\n')
    line_count = len(lines)
    file_name = path.split('/')[-1].split('.')[0]
    return {
        "file_path": path,
        "line_count": line_count,
        "keywords": [file_name],
        "metadata_json": {}
    }

def get_parser_result(path: str, content: str) -> dict:
    """
    Call the appropriate parser based on file extension and return metadata.
    Fully replaced with a powerful Tree-sitter-based parser architecture.
    """
    ext = path.split('.')[-1].lower() if '.' in path else ''
    filename = path.split('/')[-1].lower()
    
    # 1. Config & Data files
    if ext == 'json':
        parser = JsonParser(content, path)
    elif ext == 'xml':
        parser = XmlParser(content, path)
    elif ext in ['yaml', 'yml', 'toml']:
        parser = YamlTomlParser(content, path)
    elif ext in ['gradle', 'kts'] and 'build' in filename:
        parser = GradleParser(content, path)
    elif ext == 'sql':
        parser = SqlParser(content, path)
        
    # 2. Programming Languages
    elif ext in ['js', 'jsx', 'ts', 'tsx']:
        parser = JavaScriptParser(content, path)
    elif ext == 'py':
        parser = PythonParser(content, path)
    elif ext == 'java':
        parser = JavaParser(content, path)
    elif ext in ['kt', 'kts']:
        parser = KotlinParser(content, path)
    elif ext == 'go':
        parser = GoParser(content, path)
    elif ext == 'cs':
        parser = CSharpParser(content, path)
    elif ext == 'dart':
        parser = DartParser(content, path)
    elif ext in ['c', 'cpp', 'h', 'hpp', 'cc']:
        parser = CppParser(content, path)
    elif ext == 'rs':
        parser = RustParser(content, path)
    elif ext in ['swift', 'm', 'h']:
        parser = SwiftParser(content, path)
    elif ext == 'rb':
        parser = RubyParser(content, path)
    elif ext == 'php':
        parser = PhpParser(content, path)
        
    else:
        # Use default metadata extractor if no parser matches
        return generic_extract_metadata(path, content)
        
    return parser.parse()
