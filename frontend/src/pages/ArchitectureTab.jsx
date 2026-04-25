import { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { Loader2, RefreshCw, GitBranch, Sparkles, Layout, Activity, ChevronRight } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';
import ReactMarkdown from 'react-markdown';
import { projectService } from '../api';

function ArchitectureTab() {
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState('');
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
      const data = await projectService.getNetwork(sessionId);
      setGraphData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchArchitectureAnalysis = async (force = false, generateIfMissing = true) => {
    if (!sessionId) return;
    setIsAnalyzing(true);
    try {
      const data = await projectService.getArchitectureAnalysis(sessionId, { 
        force_regenerate: force,
        generate_if_missing: generateIfMissing
      });
      setAnalysis(data.analysis);
    } catch (err) {
      console.error('Analysis failed:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    if (sessionId) {
      fetchNetworkData();
      fetchArchitectureAnalysis(false, false); // Check only, don't generate if missing
    }
  }, [sessionId]);

  // 그룹별 고유 색상 할당 헬퍼 함수
  const getColor = (group) => {
    const hash = group.split('').reduce((acc, char) => char.charCodeAt(0) + ((acc << 5) - acc), 0);
    const h = hash % 360;
    return `hsl(${h}, 70%, 60%)`;
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 p-8 overflow-y-auto custom-scrollbar">
      <div className="max-w-7xl mx-auto w-full space-y-12 pb-20">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-bold mb-3">
              <GitBranch className="w-4 h-4" />
              <span>Interactive Neural Network Graph</span>
            </div>
            <h2 className="text-4xl font-black text-white tracking-tight italic uppercase">Architecture Map</h2>
            <p className="text-slate-400 mt-2 text-lg">Dynamic graph based on a physics engine. Explore the project's structural DNA.</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => { fetchNetworkData(); fetchArchitectureAnalysis(); }}
              disabled={isLoading || isAnalyzing}
              className="flex items-center gap-2 px-6 py-3 bg-slate-800 border border-slate-700 text-slate-200 rounded-2xl hover:bg-slate-700 transition-all shadow-lg active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${(isLoading || isAnalyzing) ? 'animate-spin' : ''}`} />
              Sync Analysis
            </button>
          </div>
        </div>

        {/* Graph Section */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center min-h-[600px] bg-slate-900/50 rounded-[2.5rem] border border-slate-800 shadow-2xl backdrop-blur-md">
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
            <p className="text-slate-300 font-medium text-lg">Synthesizing structure graph...</p>
          </div>
        ) : error ? (
          <div className="p-12 bg-red-900/20 border border-red-500/30 rounded-[2.5rem] text-center">
            <p className="text-red-400 font-medium text-lg">{error}</p>
            <button 
              onClick={fetchNetworkData}
              className="mt-6 px-8 py-3 bg-red-600 text-white rounded-2xl hover:bg-red-700 transition-all font-bold"
            >
              Retry Connection
            </button>
          </div>
        ) : graphData.nodes.length > 0 ? (
          <div className="space-y-12">
            <div 
              ref={containerRef}
              className="relative group bg-slate-900 rounded-[2.5rem] border border-slate-800 shadow-[0_0_80px_rgba(0,0,0,0.6)] overflow-hidden h-[700px] w-full"
            >
              <ForceGraph2D
                width={dimensions.width}
                height={dimensions.height}
                graphData={graphData}
                nodeLabel="id"
                nodeColor={node => getColor(node.group)}
                nodeRelSize={6}
                linkColor={() => 'rgba(255,255,255,0.15)'}
                linkWidth={1.2}
                linkDirectionalParticles={3}
                linkDirectionalParticleWidth={2}
                linkDirectionalParticleSpeed={0.005}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  const label = node.name;
                  const fontSize = 12/globalScale;
                  ctx.font = `bold ${fontSize}px Inter, system-ui`;
                  const textWidth = ctx.measureText(label).width;
                  const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.4);

                  ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
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
              
              <div className="absolute bottom-6 left-8 z-20 flex items-center gap-4 text-slate-400 text-xs font-bold bg-slate-950/80 px-5 py-2.5 rounded-2xl border border-white/10 backdrop-blur-xl shadow-2xl">
                <span className="flex items-center gap-1.5"><Activity className="w-3 h-3 text-emerald-400" /> Scroll to zoom</span>
                <span className="w-1.5 h-1.5 rounded-full bg-slate-800"></span>
                <span className="flex items-center gap-1.5"><Layout className="w-3 h-3 text-blue-400" /> Drag to pan</span>
              </div>
              
              <div className="absolute top-6 right-8 z-20 flex flex-col items-end gap-3 text-slate-400 text-xs font-bold bg-slate-950/80 px-6 py-5 rounded-[2rem] border border-white/10 backdrop-blur-xl shadow-2xl">
                <div className="text-white text-sm font-black uppercase tracking-widest mb-1 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    Graph Statistics
                </div>
                <div className="flex flex-col items-end gap-1">
                    <div className="flex items-center gap-2">
                        <span className="text-slate-500">Nodes (Files)</span>
                        <span className="text-blue-400 text-lg font-black">{graphData.nodes.length}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="text-slate-500">Edges (Deps)</span>
                        <span className="text-purple-400 text-lg font-black">{graphData.links.length}</span>
                    </div>
                </div>
              </div>
            </div>

            {/* AI Architecture Analysis Section */}
            <div className="space-y-6">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-indigo-500/20 rounded-2xl border border-indigo-500/30">
                        <Sparkles className="w-6 h-6 text-indigo-400" />
                    </div>
                    <div className="flex-1">
                        <div className="flex items-center justify-between">
                            <h3 className="text-2xl font-black text-white uppercase tracking-tight">AI Architecture Analysis</h3>
                            <button 
                                onClick={() => fetchArchitectureAnalysis(true)}
                                disabled={isAnalyzing}
                                className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-slate-400 hover:text-indigo-400 transition-all text-xs font-bold disabled:opacity-50"
                            >
                                <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
                                Regenerate
                            </button>
                        </div>
                        <p className="text-slate-400">Deep structural insights generated by AI architect.</p>
                    </div>
                </div>

                <div className="relative overflow-hidden bg-slate-900/50 rounded-[2.5rem] border border-white/5 shadow-2xl backdrop-blur-sm p-10 min-h-[400px]">
                    {isAnalyzing ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/40 backdrop-blur-sm z-10">
                            <div className="relative">
                                <div className="w-20 h-20 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
                                <Sparkles className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 text-indigo-400 animate-pulse" />
                            </div>
                            <p className="mt-6 text-indigo-300 font-black uppercase tracking-[0.2em] animate-pulse">Analyzing Pattern...</p>
                        </div>
                    ) : analysis ? (
                        <div className="prose prose-invert prose-indigo max-w-none 
                            prose-headings:text-white prose-headings:font-black prose-headings:tracking-tight
                            prose-h1:text-3xl prose-h1:mb-8 prose-h1:pb-4 prose-h1:border-b prose-h1:border-white/10
                            prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4 prose-h2:text-indigo-300
                            prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3 prose-h3:text-slate-200
                            prose-p:text-slate-400 prose-p:leading-relaxed prose-p:text-base
                            prose-strong:text-white prose-strong:font-bold
                            prose-code:bg-indigo-500/10 prose-code:text-indigo-300 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:before:content-none prose-code:after:content-none prose-code:font-mono prose-code:text-sm
                            prose-ul:my-6 prose-li:text-slate-400 prose-li:marker:text-indigo-500
                            prose-blockquote:border-l-indigo-500 prose-blockquote:bg-white/5 prose-blockquote:py-1 prose-blockquote:px-6 prose-blockquote:rounded-r-2xl prose-blockquote:italic prose-blockquote:text-slate-300">
                            <ReactMarkdown>{analysis}</ReactMarkdown>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full py-20 text-center">
                            <div className="w-20 h-20 bg-slate-800 rounded-3xl flex items-center justify-center mb-6">
                                <Layout className="w-10 h-10 text-slate-600" />
                            </div>
                            <h4 className="text-slate-300 text-xl font-bold mb-2">No Analysis Available</h4>
                            <p className="text-slate-500 max-w-md">Sync analysis to get path-finding insights and structural evaluations from the AI Agent.</p>
                            <button 
                                onClick={fetchArchitectureAnalysis}
                                className="mt-8 flex items-center gap-2 px-8 py-3 bg-indigo-600 text-white rounded-2xl font-black uppercase tracking-widest hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/20"
                            >
                                Generate Analysis
                            </button>
                        </div>
                    )}
                </div>
            </div>
          </div>
        ) : (
          <div className="p-32 text-center border-4 border-dashed border-slate-800 rounded-[3rem] bg-slate-900/20">
            <p className="text-slate-500 text-xl font-medium">Click sync to synthesize architecture data.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ArchitectureTab;
