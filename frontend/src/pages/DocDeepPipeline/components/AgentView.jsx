import React from "react";
import { Info, RefreshCw, CheckCircle2, ArrowRight } from "lucide-react";

const AgentView = ({ agentSteps }) => {
  return (
    <div className="w-full max-w-6xl space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
        {/* Connection Arrows Overlay (Desktop Only) */}
        <div className="hidden lg:block absolute top-[40px] left-[15%] right-[15%] h-[2px] bg-slate-800 z-0"></div>
        
        {agentSteps.map((agent, idx) => (
          <div key={agent.id} className="relative z-10 glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-emerald-500/30 transition-all group">
            <div className="w-16 h-16 rounded-2xl bg-black border border-slate-800 flex items-center justify-center mb-6 text-emerald-400 group-hover:scale-110 transition-transform">
              <span className="text-2xl">{idx + 1}</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-3 tracking-tight">{agent.title}</h3>
            <p className="text-emerald-500/80 text-sm font-bold mb-4">{agent.desc}</p>
            <p className="text-slate-400 text-sm leading-relaxed mb-6">{agent.detail}</p>
            
            <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
              <div className="text-[10px] text-emerald-500 font-black uppercase tracking-widest mb-1 flex items-center gap-1">
                <Info size={12} /> Insight
              </div>
              <p className="text-xs text-slate-300 italic">"{agent.tip}"</p>
            </div>

            {idx === 3 && (
              <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-4 py-1.5 rounded-full text-[11px] font-black animate-bounce">
                <RefreshCw size={12} /> CONDITIONAL LOOP BACK TO WRITER
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-20 glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-[80px] rounded-full"></div>
        <div className="relative z-10">
          <h2 className="text-3xl font-black text-white mb-8 tracking-tighter flex items-center gap-3">
            <CheckCircle2 className="text-emerald-500" />
            최종본 출력 (Final Output)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <p className="text-slate-300 text-lg leading-relaxed">
                리뷰어 에이전트의 승인을 받은 완벽한 <b>README.md</b>가 사용자에게 제공됩니다. 
                단순한 코드 나열이 아닌 프로젝트의 핵심 가치와 아키텍처를 전문적으로 설명하는 고품질 문서를 경험하세요.
              </p>
              <ul className="space-y-3">
                {["사용자 맞춤형 섹션 자동 구성", "프로젝트 핵심 기능(Feature) 도출", "정확한 설치 및 실행 가이드", "세련된 기술 스택 뱃지 자동 삽입"].map(item => (
                  <li key={item} className="flex items-center gap-3 text-slate-400 text-sm font-medium">
                    <ArrowRight size={14} className="text-emerald-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-black/40 rounded-3xl p-8 border border-white/5 font-mono text-[13px] text-pink-400/90 whitespace-pre-wrap leading-relaxed shadow-inner">
              # 🚀 AwesomeProject{"\n"}
              - "개발자를 위한 최고의 생산성 도구"{"\n\n"}
              ## ✨ 주요 기능{"\n"}
              - ⚡ **실시간 동기화**: WebSocket 기반...{"\n"}
              - 🔒 **안전한 인증**: JWT 기반 Oauth...{"\n\n"}
              ## 📂 폴더 구조{"\n"}
              📦 src/{"\n"}
               ┣ 📂 components{"\n"}
               ┗ 📂 utils
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentView;
