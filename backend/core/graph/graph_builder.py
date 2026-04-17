import networkx as nx

class DependencyGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph() # 방향성이 있는 그래프

    def build_graph(self, files_meta: dict):
        """
        files_meta: { "path/to/File.kt": {"package": "...", "imports": [...], ...} }
        """
        # 1. 모든 파일을 노드로 추가하고, 패키지 기반 매핑 테이블 생성
        package_map = {} # {"com.example.Service": "path/to/Service.kt"}
        
        for path, meta in files_meta.items():
            file_name = path.split("/")[-1]
            self.graph.add_node(path, label=file_name, type="file")
            
            # 패키지 + 클래스명으로 매핑 (정교하진 않지만 PoC용으로 적합)
            pkg = meta.get("package", "")
            for cls in meta.get("classes", []):
                full_identity = f"{pkg}.{cls['name']}"
                package_map[full_identity] = path

        # 2. Import 문을 분석하여 엣지(Edge, 화살표) 연결
        for path, meta in files_meta.items():
            for imp in meta.get("imports", []):
                # 만약 import 경로가 우리 프로젝트 안에 있는 파일이라면 연결
                if imp in package_map:
                    target_path = package_map[imp]
                    if path != target_path: # 자기 자신 참조 제외
                        self.graph.add_edge(path, target_path, relationship="DEPENDS_ON")

        return self.graph

    def get_summary(self):
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "top_referenced": sorted(self.graph.in_degree(), key=lambda x: x[1], reverse=True)[:5]
        }