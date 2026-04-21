import ast

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, code):
        self.code = code
        self.lines = code.split('\n')
        self.imports = []
        self.classes = []
        self.functions = []
        self.decorators = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes.append({
            "name": node.name,
            "line": node.lineno,
            "docstring": ast.get_docstring(node)
        })
        for deco in node.decorator_list:
            if isinstance(deco, ast.Name):
                self.decorators.append(deco.id)
            elif isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name):
                self.decorators.append(deco.func.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "line": node.lineno,
            "docstring": ast.get_docstring(node)
        })
        for deco in node.decorator_list:
            if isinstance(deco, ast.Name):
                self.decorators.append(deco.id)
            elif isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name):
                self.decorators.append(deco.func.id)
        self.generic_visit(node)

def parse_python_code(code: str) -> dict:
    """
    Python 코드를 AST로 파싱하여 메타데이터를 추출합니다.
    """
    lines = code.split('\n')
    line_count = len(lines)
    try:
        tree = ast.parse(code)
        analyzer = CodeAnalyzer(code)
        analyzer.visit(tree)
        
        # 키워드 조합
        keywords = list(set(
            [c["name"] for c in analyzer.classes] + 
            [f["name"] for f in analyzer.functions] + 
            analyzer.decorators
        ))

        return {
            "line_count": line_count,
            "keywords": keywords,
            "imports": analyzer.imports,
            "classes": analyzer.classes,
            "functions": analyzer.functions,
            "metadata_json": {
                "imports": analyzer.imports,
                "classes": analyzer.classes,
                "functions": analyzer.functions,
                "decorators": list(set(analyzer.decorators))
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "line_count": line_count,
            "keywords": [],
            "metadata_json": {}
        }