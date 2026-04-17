import ast

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []

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
            "lineno": node.lineno,
            "docstring": ast.get_docstring(node)
        })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions.append({
            "name": node.name,
            "lineno": node.lineno,
            "docstring": ast.get_docstring(node)
        })
        self.generic_visit(node)

def parse_python_code(code: str) -> dict:
    """
    Python 코드를 AST로 파싱하여 메타데이터를 추출합니다.
    """
    try:
        tree = ast.parse(code)
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        
        return {
            "imports": analyzer.imports,
            "classes": analyzer.classes,
            "functions": analyzer.functions
        }
    except SyntaxError as e:
        return {"error": f"SyntaxError: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}