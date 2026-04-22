import json
import networkx as nx

def test():
    g = nx.DiGraph()
    g.add_node("backend/main.py", label="main.py", type="file")
    g.add_node("backend/core/graph_builder.py", label="graph_builder.py", type="file")
    g.add_edge("backend/main.py", "backend/core/graph_builder.py", relationship="DEPENDS_ON")
    
    data = nx.node_link_data(g)
    print("Exported data:")
    print(json.dumps(data, indent=2))
    
    g2 = nx.node_link_graph(data)
    print(f"Imported nodes: {g2.number_of_nodes()}")

test()
