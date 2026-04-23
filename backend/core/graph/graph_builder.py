import networkx as nx
import os
from .resolvers.factory import ResolverFactory

class DependencyGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self, files_meta: dict):
        """
Build a graph with maximized edge detection accuracy using language-specific resolvers.
        """
        # 1. Build global index
        full_path_map = {}
        basename_map = {}
        entity_map = {}
        
        for path, meta in files_meta.items():
            parsed = meta.get("metadata_json", {}).get("parsed", {})
            full_path_map[path] = path
            
            filename = os.path.basename(path)
            base = os.path.splitext(filename)[0]
            basename_map[base] = path
            
            self.graph.add_node(path, label=filename, type="file")
            
            # Java/Kotlin packages & classes
            pkg = parsed.get("package", "")
            for cls in parsed.get("classes", []):
                cls_name = cls.get("name", "") if isinstance(cls, dict) else cls
                if cls_name:
                    if pkg:
                        entity_map[f"{pkg}.{cls_name}"] = path
                    entity_map[cls_name] = path
            
            # Infer Python module path (suffix indexing at various depths based on folder structure)
            py_module = path.replace("/", ".").replace("\\", ".")
            if py_module.endswith(".py"):
                py_module = py_module[:-3]
                entity_map[py_module] = path
                
                parts = py_module.split(".")
                for i in range(1, len(parts)):
                    suffix_module = ".".join(parts[i:])
                    if suffix_module not in entity_map:
                        entity_map[suffix_module] = path
            
            # JS/TS entities (register by filename)
            if parsed.get("language") in ["javascript", "typescript"]:
                entity_map[base] = path

        # 2. Connect edges using language-specific resolvers
        for path, meta in files_meta.items():
            parsed = meta.get("metadata_json", {}).get("parsed", {})
            language = parsed.get("language", "generic")
            imports = parsed.get("imports", [])
            
            # Obtain language-specific resolver
            resolver = ResolverFactory.get_resolver(
                language, 
                full_path_map, 
                basename_map, 
                entity_map
            )
            
            for imp in imports:
                result = resolver.resolve(path, imp)
                target_paths = result if isinstance(result, list) else [result]
                
                for target_path in target_paths:
                    if target_path and target_path != path:
                        self.graph.add_edge(path, target_path, relationship="DEPENDS_ON")

        return self.graph

    def get_summary(self):
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "top_referenced": sorted(self.graph.in_degree(), key=lambda x: x[1], reverse=True)[:5]
        }