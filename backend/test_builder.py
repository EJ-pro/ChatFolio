import sys
import os

from core.graph.graph_builder import DependencyGraphBuilder

def test_builder():
    all_meta = {
        "backend/main.py": {
            "metadata_json": {
                "parsed": {
                    "language": "python",
                    "imports": ["from core.parser.factory import get_parser_result"]
                }
            }
        },
        "backend/core/parser/factory.py": {
            "metadata_json": {
                "parsed": {
                    "language": "python",
                    "imports": []
                }
            }
        }
    }
    
    builder = DependencyGraphBuilder()
    graph = builder.build_graph(all_meta)
    
    print("Nodes:", graph.number_of_nodes())
    print("Edges:", graph.number_of_edges())
    print("Graph Data:", graph.edges(data=True))

if __name__ == "__main__":
    test_builder()
