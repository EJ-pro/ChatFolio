import sys
import os
import json
import networkx as nx

# Add current directory to path so we can import from backend
sys.path.append('.')
from database.database import SessionLocal
from database.models import Project, ProjectFile
from core.graph.graph_builder import DependencyGraphBuilder

def diagnose():
    db = SessionLocal()
    try:
        # 1. 최신 프로젝트 가져오기
        project = db.query(Project).order_by(Project.id.desc()).first()
        if not project:
            print("❌ 프로젝트를 찾을 수 없습니다.")
            return

        print(f"🔍 프로젝트 진단 시작: {project.repo_url} (ID: {project.id})")
        print(f"📊 현재 DB 상태: 노드 {project.node_count}개, 엣지 {project.edge_count}개")

        # 2. 파일 메타데이터 로드
        files = db.query(ProjectFile).filter(ProjectFile.project_id == project.id).all()
        files_meta = {}
        for f in files:
            files_meta[f.file_path] = {
                "metadata_json": f.metadata_json if f.metadata_json else {}
            }

        if not files_meta:
            print("❌ 로드된 파일 메타데이터가 없습니다.")
            return

        print(f"📁 총 {len(files_meta)}개의 파일 메타 데이터를 로드했습니다.")

        # 3. 그래프 구축 시뮬레이션
        builder = DependencyGraphBuilder()
        graph = builder.build_graph(files_meta)
        
        print("\n--- 결과 분석 ---")
        print(f"✅ 구축된 그래프 노드 수: {graph.number_of_nodes()}")
        print(f"✅ 구축된 그래프 엣지 수: {graph.number_of_edges()}")

        if graph.number_of_edges() == 0:
            print("\n⚠️ 엣지가 여전히 0개입니다. 원인 분석 중...")
            
            count = 0
            for path, meta in list(files_meta.items())[:10]:
                parsed = meta.get("metadata_json", {}).get("parsed", {})
                imports = parsed.get("imports", [])
                if imports:
                    print(f"\n파일: {path} (언어: {parsed.get('language')})")
                    print(f"  임포트 목록: {imports}")
                    count += 1
            if count == 0:
                print("❌ 분석된 모든 파일에 'imports' 데이터가 비어 있습니다! (파서 단계의 문제)")
            else:
                print("\n🤔 임포트 데이터는 존재하나, 리졸버가 매칭에 실패하고 있습니다. (인덱싱/해석 단계의 문제)")
        else:
            print("\n🎉 엣지 생성이 확인되었습니다! 이제 실제 분석만 돌리면 됩니다.")

    except Exception as e:
        print(f"❌ 진단 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
