import React, { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { projectService } from "../api";
import { 
  Database, Layers, Cpu, Binary, RefreshCw, Sparkles, 
  Terminal, Info, CheckCircle2, Loader2, Search, Activity,
  Lock, CloudDownload, Scissors, Fingerprint, BarChart3,
  MessageSquare, Brain, Bot, ArrowRight
} from "lucide-react";

export default function PipelineTab() {
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  const [pipeline, setPipeline] = useState(null);
  const [activeNode, setActiveNode] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (sessionId) fetchPipeline();
  }, [sessionId]);

  const fetchPipeline = async () => {
    try {
      setIsLoading(true);
      const data = await projectService.getProjectPipeline(sessionId);
      if (data && data.steps) {
        setPipeline(data);
      }
    } catch (err) {
      console.error("Pipeline fetch failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-slate-950 p-20">
        <div className="relative">
          <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full"></div>
          <Loader2 className="w-16 h-16 text-emerald-500 animate-spin mb-6 relative z-10" />
        </div>
        <p className="text-slate-400 animate-pulse font-black tracking-[0.2em] text-sm uppercase">AI Architecture Tracing...</p>
      </div>
    );
  }

  const steps = pipeline?.steps || [];
  
  if (steps.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-slate-950 p-20 text-center">
        <Activity className="w-16 h-16 text-slate-700 mb-6" />
        <h2 className="text-2xl font-bold text-white mb-2">No Pipeline Data</h2>
        <p className="text-slate-500">Could not infer a clear execution pipeline for this project.</p>
        <button onClick={fetchPipeline} className="mt-6 px-6 py-2 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-500 transition-all">
          Retry Analysis
        </button>
      </div>
    );
  }

  const active = steps[activeNode];

  // Map icon strings or logic to Lucide components
  const getIcon = (id) => {
    const icons = {
      auth: <Lock size={22} />,
      scan: <Binary size={22} />,
      fetch: <CloudDownload size={22} />,
      chunk: <Scissors size={22} />,
      embed: <Fingerprint size={22} />,
      indexing: <Database size={22} />,
      retrieval: <Search size={22} />,
      ranking: <BarChart3 size={22} />,
      inference: <Cpu size={22} />,
      logic: <Brain size={22} />,
      api: <Activity size={22} />,
      db: <Database size={22} />
    };
    return icons[id.toLowerCase()] || <Layers size={22} />;
  };

  return (
    <div className="flex-1 bg-[#030712] text-[#e2e8f0] p-6 md:p-10 flex flex-col items-center overflow-y-auto custom-scrollbar" style={{ fontFamily: "Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}>
      {/* Header Area */}
      <div className="w-full max-w-6xl mb-12 flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[10px] text-emerald-400 font-black uppercase tracking-widest mb-4">
            <Activity size={12} /> Dynamic Execution Pipeline
          </div>
          <h1 className="text-3xl md:text-5xl font-black tracking-tight text-white mb-2 leading-tight">
            Project<span className="text-emerald-400">Flow</span>
          </h1>
          <p className="text-slate-400 text-lg">Inferred business logic and data lifecycle from analyzed source code</p>
        </div>
        
        <div className="flex gap-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
            <div className="text-[10px] text-slate-500 mb-1 font-black tracking-widest uppercase">Pipeline Stages</div>
            <div className="text-2xl font-black text-slate-100">{steps.length} Phases</div>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
            <div className="text-[10px] text-slate-500 mb-1 font-black tracking-widest uppercase">System Status</div>
            <div className="text-2xl font-black text-emerald-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></div> ACTIVE
            </div>
          </div>
        </div>
      </div>

      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left Navigation */}
        <div className="lg:col-span-5 relative flex flex-col gap-3">
          <div className="absolute left-7 top-10 bottom-10 w-[2px] bg-slate-800/30 z-0"></div>
          {steps.map((step, idx) => (
            <div key={step.id} className="relative z-10 flex gap-5 cursor-pointer group" onClick={() => setActiveNode(idx)}>
              <div className="flex flex-col items-center mt-1">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-xl ${activeNode === idx ? 'scale-110 ring-4 ring-offset-4 ring-offset-[#030712] ring-opacity-20 border-2' : 'bg-slate-900/80 border border-slate-800 opacity-50 group-hover:opacity-100 group-hover:bg-slate-800'}`} style={{ backgroundColor: activeNode === idx ? `${step.color}20` : '', borderColor: activeNode === idx ? step.color : '', color: activeNode === idx ? step.color : '#64748b', boxShadow: activeNode === idx ? `0 0 30px ${step.color}30` : '' }}>
                  {getIcon(step.id)}
                </div>
                {idx < steps.length - 1 && <div className={`w-[2px] h-full my-1 transition-colors ${activeNode >= idx ? 'bg-emerald-500/40' : 'bg-slate-800'}`}></div>}
              </div>
              <div className={`flex-1 p-4 rounded-2xl border transition-all duration-300 ${activeNode === idx ? 'bg-slate-900/80 border-slate-700 shadow-2xl translate-x-1' : 'bg-transparent border-transparent opacity-50 group-hover:opacity-100 group-hover:translate-x-1'}`}>
                <div className="text-[10px] font-black tracking-widest mb-1 uppercase" style={{ color: step.color }}>Phase {idx + 1}</div>
                <div className={`font-bold text-lg ${activeNode === idx ? 'text-white' : 'text-slate-400'}`}>{step.title}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Right Detail Panel */}
        <div className="lg:col-span-7">
          <div className="sticky top-8 bg-slate-900/60 backdrop-blur-2xl border border-slate-800 rounded-[2.5rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative overflow-hidden h-full min-h-[600px] flex flex-col">
            <div className="absolute -top-24 -right-24 w-96 h-96 blur-[120px] rounded-full opacity-30 pointer-events-none transition-colors duration-1000" style={{ backgroundColor: active.color }}></div>
            
            <div className="relative z-10 border-b border-slate-800/50 pb-8 mb-8">
              <div className="flex items-center gap-5 mb-3">
                <div className="p-3 rounded-2xl bg-black border border-slate-800 shadow-inner" style={{ color: active.color }}>{getIcon(active.id)}</div>
                <div>
                  <h2 className="text-3xl font-black text-white tracking-tight">{active.title}</h2>
                  <p className="text-slate-400 text-base mt-2 font-medium">{active.desc}</p>
                </div>
              </div>
            </div>

            <div className="relative z-10 flex-1 flex flex-col gap-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                  <div className="text-[10px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2"><Terminal size={14} /> Implementation Context</div>
                  <div className="font-bold text-emerald-400 text-sm font-mono break-all leading-relaxed truncate">{active.file}</div>
                </div>
                <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                  <div className="text-[10px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2"><Layers size={14} /> Technologies</div>
                  <div className="flex flex-wrap gap-2">
                    {active.tech.map(t => (
                      <span key={t} className="px-3 py-1 bg-slate-800/80 rounded-lg text-[10px] font-bold shadow-sm" style={{ color: active.color }}>{t}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex-1 bg-black/40 rounded-3xl border border-slate-800/80 p-8 mt-2 flex flex-col shadow-2xl ring-1 ring-white/5">
                <div className="text-[10px] text-slate-500 mb-6 tracking-widest font-black uppercase flex items-center gap-2"><Info size={16} /> Stage Execution Details</div>
                <div className="space-y-5 mb-10">
                  {active.details.actions.map((act, i) => (
                    <div key={i} className="flex items-start gap-4 text-[14px] text-slate-300 leading-relaxed font-medium">
                      <CheckCircle2 size={18} className="mt-1 shrink-0" style={{ color: active.color }} />
                      <span>{act}</span>
                    </div>
                  ))}
                </div>

                <div className="mt-auto pt-8 border-t border-slate-800/50">
                  <div className="text-[10px] text-slate-500 mb-4 tracking-widest font-black uppercase flex items-center justify-between">
                    <span>Data Object Model (DOM)</span>
                    <span className="text-emerald-500/70 bg-emerald-500/10 px-2 py-0.5 rounded text-[9px] font-black">INFERRED_INSTANCE</span>
                  </div>
                  <pre className="bg-black/80 border border-slate-800 p-6 rounded-2xl text-[12px] overflow-x-auto text-pink-400/90 font-mono shadow-inner leading-relaxed custom-scrollbar max-h-[180px]">
                    <code>{JSON.stringify(active.details.payload, null, 2)}</code>
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
