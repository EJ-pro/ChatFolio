import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { Loader2, RefreshCw, GitBranch } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';

function ArchitectureTab() {
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef(null);

  // 컨테이너 크기에 맞춰 그래프 크기 자동 조절
  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
    }
    
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [graphData]);

  const fetchNetworkData = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/generate/network', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error('그래프 데이터를 가져오는 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setGraphData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNetworkData();
  }, [sessionId]);

  // 그룹별 고유 색상 할당 헬퍼 함수
  const getColor = (group) => {
    const hash = group.split('').reduce((acc, char) => char.charCodeAt(0) + ((acc << 5) - acc), 0);
    const h = hash % 360;
    return `hsl(${h}, 70%, 60%)`;
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 p-8 overflow-y-auto">
      <div className="max-w-7xl mx-auto w-full space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-bold mb-3">
              <GitBranch className="w-4 h-4" />
              <span>Interactive Neural Network Graph</span>
            </div>
            <h2 className="text-3xl font-bold text-white tracking-tight">아키텍처 맵 (LangSmith 스타일)</h2>
            <p className="text-slate-400 mt-1">물리 엔진 기반의 동적 그래프입니다. 노드를 드래그하고 줌인하여 상세 구조를 탐색하세요.</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={fetchNetworkData}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 border border-slate-700 text-slate-200 rounded-xl hover:bg-slate-700 transition-colors shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              데이터 새로고침
            </button>
          </div>
        </div>

        {/* Content Area */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center min-h-[600px] bg-slate-900/50 rounded-3xl border border-slate-800 shadow-sm backdrop-blur-md">
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
            <p className="text-slate-300 font-medium">초고속 엔진으로 구조 데이터를 로드하는 중입니다...</p>
            <p className="text-slate-500 text-sm mt-1">AI 생성 대기 없이 즉시 렌더링됩니다.</p>
          </div>
        ) : error ? (
          <div className="p-8 bg-red-900/20 border border-red-500/30 rounded-3xl text-center">
            <p className="text-red-400 font-medium">{error}</p>
            <button 
              onClick={fetchNetworkData}
              className="mt-4 px-6 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors"
            >
              재시도
            </button>
          </div>
        ) : graphData.nodes.length > 0 ? (
          <div className="space-y-6">
            <div 
              ref={containerRef}
              className="relative group bg-slate-900 rounded-3xl border border-slate-800 shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden h-[700px] w-full"
            >
              <ForceGraph2D
                width={dimensions.width}
                height={dimensions.height}
                graphData={graphData}
                nodeLabel="id"
                nodeColor={node => getColor(node.group)}
                nodeRelSize={6}
                linkColor={() => 'rgba(255,255,255,0.2)'}
                linkWidth={1.5}
                linkDirectionalParticles={2}
                linkDirectionalParticleWidth={2}
                linkDirectionalParticleSpeed={0.005}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  const label = node.name;
                  const fontSize = 12/globalScale;
                  ctx.font = `${fontSize}px Sans-Serif`;
                  const textWidth = ctx.measureText(label).width;
                  const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

                  ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
                  ctx.beginPath();
                  ctx.roundRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1], 4);
                  ctx.fill();

                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillStyle = node.color || '#fff';
                  ctx.fillText(label, node.x, node.y);

                  node.__bckgDimensions = bckgDimensions; 
                }}
                nodePointerAreaPaint={(node, color, ctx) => {
                  ctx.fillStyle = color;
                  const bckgDimensions = node.__bckgDimensions;
                  bckgDimensions && ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);
                }}
              />
              
              <div className="absolute bottom-4 left-6 z-20 flex items-center gap-2 text-slate-400 text-xs font-medium bg-slate-900/80 px-3 py-1.5 rounded-lg border border-white/5 backdrop-blur-md">
                <span>🖱️ 휠로 확대/축소</span>
                <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                <span>👋 드래그로 맵 이동</span>
                <span className="w-1 h-1 rounded-full bg-slate-600"></span>
                <span>👆 노드를 잡고 이동</span>
              </div>
              
              <div className="absolute top-4 right-6 z-20 flex flex-col items-end gap-2 text-slate-400 text-xs font-medium bg-slate-900/80 px-4 py-3 rounded-xl border border-white/5 backdrop-blur-md">
                <div className="text-white font-bold mb-1">통계</div>
                <div>노드(파일): {graphData.nodes.length}개</div>
                <div>의존성(엣지): {graphData.links.length}개</div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-20 text-center border-2 border-dashed border-slate-700 rounded-3xl">
            <p className="text-slate-400">데이터를 불러오려면 새로고침 버튼을 눌러주세요.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ArchitectureTab;
