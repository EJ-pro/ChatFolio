import React from "react";
import { RefreshCw, Search, Cpu, Sparkles } from "lucide-react";
import MermaidDiagram from "./MermaidDiagram.jsx";

const SequenceView = ({ sequenceChart }) => {
  return (
    <div className="w-full max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500/50 to-blue-500/50"></div>
        
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-3xl font-black text-white mb-2 tracking-tighter flex items-center gap-3">
                <RefreshCw className="text-emerald-500" />
                전체 시스템 시퀀스 (Full System Sequence)
              </h2>
              <p className="text-slate-400 text-sm">사용자 요청부터 최종 결과물 출력까지의 시간순 실행 흐름</p>
            </div>
            <div className="flex items-center gap-3 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Live Flow Logic</span>
            </div>
          </div>

          <div className="bg-slate-950/80 rounded-3xl p-8 border border-white/5 shadow-2xl overflow-x-auto custom-scrollbar">
            <MermaidDiagram chart={sequenceChart} />
          </div>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
              <h4 className="text-emerald-400 font-bold mb-2 flex items-center gap-2">
                <Search size={16} /> 캐싱 최적화
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                동일한 커밋 SHA에 대해서는 파싱 과정을 생략하고 즉시 응답하여 서버 리소스를 보존합니다.
              </p>
            </div>
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
              <h4 className="text-blue-400 font-bold mb-2 flex items-center gap-2">
                <Cpu size={16} /> 스트리밍 분석
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                대규모 레포지토리도 Generator 패턴을 통해 메모리 부하 없이 실시간으로 파싱합니다.
              </p>
            </div>
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
              <h4 className="text-purple-400 font-bold mb-2 flex items-center gap-2">
                <Sparkles size={16} /> 에이전트 협업
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                단순 LLM 호출이 아닌, 4가지 전문 에이전트의 상호 검토 과정을 거쳐 품질을 보장합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SequenceView;
