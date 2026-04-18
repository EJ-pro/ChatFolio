import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import mermaid from 'mermaid';
import { Loader2, Download, Copy, RefreshCw } from 'lucide-react';

// Mermaid 렌더링을 위한 별도 컴포넌트
const MermaidViewer = ({ chart }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (chart && ref.current) {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'neutral',
        securityLevel: 'loose',
        fontFamily: 'Inter, system-ui, sans-serif',
      });
      
      // 기존 내용 삭제 후 재렌더링
      ref.current.removeAttribute('data-processed');
      ref.current.innerHTML = chart;
      mermaid.contentLoaded();
    }
  }, [chart]);

  return (
    <div className="flex justify-center p-4 bg-white rounded-2xl border border-slate-100 shadow-inner overflow-auto min-h-[400px]">
      <div className="mermaid" ref={ref}>
        {chart}
      </div>
    </div>
  );
};

function ArchitectureTab() {
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  
  const [diagramCode, setDiagramCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDiagram = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/generate/diagram', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error('다이어그램 생성 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setDiagramCode(data.mermaid_code);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagram();
  }, [sessionId]);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(diagramCode);
    alert('Mermaid 코드가 클립보드에 복사되었습니다.');
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 p-8 overflow-y-auto">
      <div className="max-w-6xl mx-auto w-full space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">아키텍처 맵</h2>
            <p className="text-slate-500 mt-1">AI가 분석한 프로젝트의 계층 구조와 의존성 다이어그램입니다.</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={fetchDiagram}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              다시 생성
            </button>
            <button 
              onClick={copyToClipboard}
              disabled={!diagramCode}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors shadow-md disabled:opacity-50"
            >
              <Copy className="w-4 h-4" />
              코드 복사
            </button>
          </div>
        </div>

        {/* Content Area */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center min-h-[500px] bg-white rounded-3xl border border-slate-100 shadow-sm">
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-4" />
            <p className="text-slate-500 font-medium">AI가 아키텍처를 시각화하는 중입니다...</p>
            <p className="text-slate-400 text-sm mt-1">규모에 따라 수십 초가 소요될 수 있습니다.</p>
          </div>
        ) : error ? (
          <div className="p-8 bg-red-50 border border-red-100 rounded-3xl text-center">
            <p className="text-red-600 font-medium">{error}</p>
            <button 
              onClick={fetchDiagram}
              className="mt-4 px-6 py-2 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors"
            >
              재시도
            </button>
          </div>
        ) : diagramCode ? (
          <div className="space-y-6">
            <MermaidViewer chart={diagramCode} />
            
            <div className="bg-slate-900 rounded-2xl p-6 overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <span className="text-slate-400 text-sm font-mono">Mermaid Syntax</span>
                <span className="px-2 py-0.5 bg-slate-800 text-slate-500 rounded text-xs font-mono uppercase tracking-widest">Read Only</span>
              </div>
              <pre className="text-blue-300 font-mono text-sm overflow-x-auto whitespace-pre-wrap leading-relaxed">
                {diagramCode}
              </pre>
            </div>
          </div>
        ) : (
          <div className="p-20 text-center border-2 border-dashed border-slate-200 rounded-3xl">
            <p className="text-slate-400">다이어그램을 생성하려면 '다시 생성' 버튼을 눌러주세요.</p>
          </div>
        )}

      </div>
    </div>
  );
}

export default ArchitectureTab;
