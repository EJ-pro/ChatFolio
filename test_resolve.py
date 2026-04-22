import os

def test_resolve():
    path_main = "backend/main.py"
    path_factory = "backend/core/parser/factory.py"
    
    entity_map = {}
    
    # Simulate DB
    for path in [path_main, path_factory]:
        py_module = path.replace("/", ".").replace("\\", ".")
        if py_module.endswith(".py"):
            py_module = py_module[:-3]
            entity_map[py_module] = path
            parts = py_module.split(".")
            for i in range(1, len(parts)):
                suffix_module = ".".join(parts[i:])
                if suffix_module not in entity_map:
                    entity_map[suffix_module] = path

    print("Entity map for factory:", {k: v for k, v in entity_map.items() if v == path_factory})

    import_str = "from core.parser.factory import get_parser_result"
    targets = []
    if " import " in import_str:
        parts = import_str.split(" import ")
        imp_module = parts[0].replace("from ", "").strip()
        imp_symbols = [s.strip() for s in parts[1].split(",")]
        
        for sym in imp_symbols:
            full_module = f"{imp_module}.{sym}"
            if full_module in entity_map:
                targets.append(entity_map[full_module])
            elif sym in entity_map:
                targets.append(entity_map[sym])
        
        if imp_module in entity_map:
            targets.append(entity_map[imp_module])

    print("Targets found:", targets)

test_resolve()
