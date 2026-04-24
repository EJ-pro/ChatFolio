import React from "react";
import { MessageSquare, Search, Layers, Sparkles } from "lucide-react";
import MermaidDiagram from "./MermaidDiagram.jsx";

const DashboardView = ({ dashboardChart }) => {
  return (
    <div className="w-full max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500/50 to-purple-500/50"></div>
        
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-3xl font-black text-white mb-2 tracking-tighter flex items-center gap-3">
                <MessageSquare className="text-blue-500" />
                대시보드 지능형 질의 흐름 (Dashboard RAG Flow)
              </h2>
              <p className="text-slate-400 text-sm">사용자 질문에 대한 의도 파악 및 아키텍처 기반 심층 답변 생성 과정</p>
            </div>
            <div className="flex items-center gap-3 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
              <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">RAG Intelligence</span>
            </div>
          </div>

          <div className="bg-slate-950/80 rounded-3xl p-8 border border-white/5 shadow-2xl overflow-x-auto custom-scrollbar">
            <MermaidDiagram chart={dashboardChart} />
          </div>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
              <h4 className="text-blue-400 font-bold mb-2 flex items-center gap-2">
                <Search size={16} /> 의도 기반 키워드
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                단순 키워드 매칭을 넘어 LLM을 통해 질문의 기술적 의도를 파악하고 핵심 키워드 간의 상관관계를 분석합니다.
              </p>
            </div>
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
              <h4 className="text-purple-400 font-bold mb-2 flex items-center gap-2">
                <Layers size={16} /> 아키텍처 매핑
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                검색된 코드 조각이 전체 시스템 아키텍처에서 어떤 노드(기능)에 해당하는지 실시간으로 대조합니다.
              </p>
            </div>
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
              <h4 className="text-emerald-400 font-bold mb-2 flex items-center gap-2">
                <Sparkles size={16} /> 컨텍스트 추론
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                단일 파일 분석이 아닌, 관련 모듈 간의 의존성 관계를 고려하여 사용자에게 종합적인 기술 답변을 제공합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
