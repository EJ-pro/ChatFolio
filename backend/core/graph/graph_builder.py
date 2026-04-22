import networkx as nx

class DependencyGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph() # 방향성이 있는 그래프

    def build_graph(self, files_meta: dict):
        """
        files_meta: { "path/to/File.kt": {"metadata_json": {"parsed": {"imports": [], "classes": []}}} }
        """
        package_map = {}
        basename_map = {}
        
        for path, meta in files_meta.items():
            parsed = meta.get("metadata_json", {}).get("parsed", {})
            file_name = path.split("/")[-1]
            base_name = file_name.split(".")[0] # 확장자 제외
            
            basename_map[base_name] = path
            self.graph.add_node(path, label=file_name, type="file")
            
            pkg = parsed.get("package", "")
            for cls in parsed.get("classes", []):
                cls_name = cls.get("name", "") if isinstance(cls, dict) else cls
                if pkg:
                    package_map[f"{pkg}.{cls_name}"] = path
                package_map[cls_name] = path # 패키지 없이 쌩 클래스명만 있는 경우

        # 2. Import 문을 분석하여 엣지(Edge, 화살표) 연결
        for path, meta in files_meta.items():
            parsed = meta.get("metadata_json", {}).get("parsed", {})
            
            # 파이썬, JS/TS 등 대부분의 언어가 imports 리스트를 가지고 있음
            imports = parsed.get("imports", [])
            for imp in imports:
                target_path = None
                
                # 1) 패키지 매핑 (자바/코틀린 등)
                if imp in package_map:
                    target_path = package_map[imp]
                else:
                    # 2) 파일명 기반 매핑 (JS/TS의 상대경로, Python의 모듈 임포트 등)
                    imp_basename = imp.split("/")[-1].split(".")[0]
                    # Python의 경우 from backend.database import models 처럼 마지막이 대상
                    imp_basename = imp_basename.split(".")[-1]
                    
                    if imp_basename in basename_map:
                        target_path = basename_map[imp_basename]
                
                if target_path and target_path != path:
                    self.graph.add_edge(path, target_path, relationship="DEPENDS_ON")

        return self.graph

    def get_summary(self):
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "top_referenced": sorted(self.graph.in_degree(), key=lambda x: x[1], reverse=True)[:5]
        }