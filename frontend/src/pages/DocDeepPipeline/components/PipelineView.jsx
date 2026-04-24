import React from "react";
import { Terminal, Layers, Info, CheckCircle2 } from "lucide-react";

const PipelineView = ({ steps, activeNode, setActiveNode, active }) => {
  return (
    <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-10">
      {/* Left Side: Pipeline Navigation */}
      <div className="lg:col-span-5 relative flex flex-col gap-3">
        <div className="absolute left-7 top-10 bottom-10 w-[2px] bg-slate-800/50 z-0"></div>
        
        {steps.map((step, idx) => (
          <div 
            key={step.id} 
            className="relative z-10 flex gap-5 cursor-pointer group"
            onClick={() => setActiveNode(idx)}
          >
            <div className="flex flex-col items-center mt-1">
              <div 
                className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-xl ${
                  activeNode === idx 
                  ? 'scale-110 ring-4 ring-offset-4 ring-offset-[#030712] ring-opacity-20 border-2' 
                  : 'bg-slate-900/80 border border-slate-800 opacity-50 group-hover:opacity-100 group-hover:bg-slate-800'
                }`}
                style={{
                  backgroundColor: activeNode === idx ? `${step.color}20` : '',
                  borderColor: activeNode === idx ? step.color : '',
                  color: activeNode === idx ? step.color : '#64748b',
                  boxShadow: activeNode === idx ? `0 0 30px ${step.color}30` : '',
                  ringColor: activeNode === idx ? step.color : 'transparent'
                }}
              >
                {step.icon}
              </div>
              {idx < steps.length - 1 && (
                <div className={`w-[2px] h-full my-1 transition-colors ${activeNode >= idx ? 'bg-emerald-500/40' : 'bg-slate-800'}`}></div>
              )}
            </div>
            
            <div className={`flex-1 p-4 rounded-2xl border transition-all duration-300 ${
              activeNode === idx 
              ? 'bg-slate-900 border-slate-700 shadow-2xl translate-x-1' 
              : 'bg-transparent border-transparent opacity-50 group-hover:opacity-100 group-hover:translate-x-1'
            }`}>
              <div className="text-[11px] font-black tracking-widest mb-1 uppercase" style={{ color: step.color }}>
                Step 0{idx + 1}
              </div>
              <div className={`font-bold text-lg ${activeNode === idx ? 'text-white' : 'text-slate-400'}`}>
                {step.title}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Right Side: Step Insights */}
      <div className="lg:col-span-7">
        <div className="sticky top-8 bg-slate-900/60 backdrop-blur-2xl border border-slate-800 rounded-[2.5rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative overflow-hidden h-full min-h-[650px] flex flex-col">
          
          <div 
            className="absolute -top-24 -right-24 w-96 h-96 blur-[120px] rounded-full opacity-30 pointer-events-none transition-colors duration-1000"
            style={{ backgroundColor: active.color }}
          ></div>

          <div className="relative z-10 border-b border-slate-800 pb-8 mb-8">
            <div className="flex items-center gap-5 mb-3">
              <div className="p-3 rounded-2xl bg-black border border-slate-800 shadow-inner" style={{ color: active.color }}>
                {active.icon}
              </div>
              <div>
                <h2 className="text-3xl font-black text-white tracking-tight">{active.title}</h2>
                <p className="text-slate-400 text-base mt-2 font-medium">{active.desc}</p>
              </div>
            </div>
          </div>

          <div className="relative z-10 flex-1 flex flex-col gap-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                <div className="text-[11px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2">
                  <Terminal size={14} /> 실행 파일 (Source)
                </div>
                <div className="font-bold text-emerald-400 text-sm font-mono break-all leading-relaxed">
                  {active.file}
                </div>
              </div>

              <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                <div className="text-[11px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2">
                  <Layers size={14} /> 핵심 기술 (Core Tech)
                </div>
                <div className="flex flex-wrap gap-2">
                  {active.tech.map(t => (
                    <span key={t} className="px-3 py-1 bg-slate-800/80 rounded-lg text-[11px] font-bold shadow-sm" style={{ color: active.color }}>
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex-1 bg-black/40 rounded-3xl border border-slate-800/80 p-8 mt-2 flex flex-col shadow-2xl ring-1 ring-white/5">
              <div className="text-[11px] text-slate-500 mb-6 tracking-widest font-black uppercase flex items-center gap-2">
                <Info size={16} /> 상세 동작 로직 (Internal Logic)
              </div>
              
              <div className="space-y-5 mb-10">
                {active.details.actions.map((act, i) => (
                  <div key={i} className="flex items-start gap-4 text-[15px] text-slate-200 leading-relaxed font-medium">
                    <CheckCircle2 size={18} className="mt-1 shrink-0" style={{ color: active.color }} />
                    <span>{act}</span>
                  </div>
                ))}
              </div>

              <div className="mt-auto pt-8 border-t border-slate-800">
                <div className="text-[11px] text-slate-500 mb-4 tracking-widest font-black uppercase flex items-center justify-between">
                  <span>데이터 구조 (Data Shape)</span>
                  <span className="text-emerald-500/70 bg-emerald-500/10 px-2 py-0.5 rounded text-[9px]">LIVE_INSTANCE</span>
                </div>
                <pre className="bg-black/80 border border-slate-800 p-6 rounded-2xl text-[12px] overflow-x-auto text-pink-400 font-mono shadow-inner leading-relaxed custom-scrollbar max-h-[180px]">
                  <code>{JSON.stringify(active.details.payload, null, 2)}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelineView;
