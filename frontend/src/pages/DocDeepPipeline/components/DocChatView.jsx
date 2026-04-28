import React from "react";
import { MessageSquare, Search, Layers, Sparkles } from "lucide-react";
import MermaidDiagram from "../DocDeepPipeline.jsx"; // We can import the MermaidDiagram from DocDeepPipeline or create an ad-hoc wrapper, but let's check how other components import it.

const docChatChart = `
graph TD
    User([1. 사용자 질문]) --> API["2. /chat 엔드포인트 (FastAPI)"]
    API --> Engine["3. ChatFolioEngine 호출"]
    
    subgraph "하이브리드 검색 (Retrieval)"
        Engine --> VectorSearch["4-1. 의미 기반 검색 (ChromaDB + BGE-M3)"]
        Engine --> BM25Search["4-2. 키워드 기반 검색 (BM25)"]
        VectorSearch --> Merge["5. 결과 결합 및 중복 제거 (Top 20)"]
        BM25Search --> Merge
    end

    subgraph "리랭킹 및 최적화 (Reranking & Context)"
        Merge --> Reranker["6. AI 리랭커 (Qwen-7B)"]
        Reranker --> TopDocs["최적의 코드 스니펫 8개 선별"]
        TopDocs --> Context["7. 컨텍스트 조립 (토큰 예산: 12,000자 제한)"]
    end

    subgraph "답변 생성 및 자가 검증 (Generation & Evaluation)"
        Context --> LLM["8. 최종 답변 생성 (Qwen-7B)"]
        LLM --> Evaluator["9. 자가 검증 (Self-Evaluation)"]
    end

    Evaluator --> FinalAnswer([10. 사용자에게 최종 답변 반환])
`;

const DocChatView = ({ MermaidDiagramComponent }) => {
  return (
    <div className="w-full max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500/50 to-blue-500/50"></div>
        
        <div className="relative z-10">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-3xl font-black text-white mb-2 tracking-tighter flex items-center gap-3">
                <MessageSquare className="text-emerald-400" />
                Doc Chat 답변 생성 프로세스 (RAG Pipeline)
              </h2>
              <p className="text-slate-400 text-sm">하이브리드 검색, AI 리랭킹 및 자가 검증을 통한 신뢰도 높은 응답 생성</p>
            </div>
            <div className="flex items-center gap-3 bg-black/40 px-4 py-2 rounded-xl border border-white/5">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
              <span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Doc Chat Pipeline</span>
            </div>
          </div>

          <div className="bg-slate-950/80 rounded-3xl p-8 border border-white/5 shadow-2xl overflow-x-auto custom-scrollbar flex justify-center">
            {MermaidDiagramComponent ? <MermaidDiagramComponent chart={docChatChart} /> : <div>Loading Chart...</div>}
          </div>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5 hover:border-emerald-500/20 transition-all">
              <h4 className="text-blue-400 font-bold mb-2 flex items-center gap-2">
                <Search size={16} /> 하이브리드 검색
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                ChromaDB 기반 의미 검색(BGE-M3)과 텍스트 매칭 중심의 BM25 검색을 결합하여 후보군을 꼼꼼히 탐색합니다.
              </p>
            </div>
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5 hover:border-emerald-500/20 transition-all">
              <h4 className="text-purple-400 font-bold mb-2 flex items-center gap-2">
                <Layers size={16} /> AI 리랭커 (Qwen-7B)
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                20개의 후보 스니펫 중 질문 해결에 가장 적합한 8개의 정예 코드 조각을 LLM을 통해 스마트하게 재정렬합니다.
              </p>
            </div>
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5 hover:border-emerald-500/20 transition-all">
              <h4 className="text-emerald-400 font-bold mb-2 flex items-center gap-2">
                <Sparkles size={16} /> 컨텍스트 최적화
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                12,000자 제한 내에서 연관된 의존성 경로 및 메타데이터를 유기적으로 조합하여 완성도 높은 맥락을 제공합니다.
              </p>
            </div>
            <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5 hover:border-emerald-500/20 transition-all">
              <h4 className="text-pink-400 font-bold mb-2 flex items-center gap-2">
                <MessageSquare size={16} /> 자가 검증 (Evaluation)
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                답변이 코드 영역을 벗어났거나 거짓(Hallucination)이 없는지 사후 평가하여 고품질 가이드를 보장합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocChatView;
