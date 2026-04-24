import React, { useState, useEffect, useRef } from "react";
import mermaid from "mermaid";
import { 
  Database, Github, Braces, Layers, Link2, 
  Cpu, FileCode2, Code, ArrowRight, Share2, Info, CheckCircle2,
  Lock, Search, CloudDownload, Terminal, BarChart3, Binary, RefreshCw, Sparkles, MessageSquare,
  Scissors, Fingerprint, ShieldCheck, Brain, Bot
} from "lucide-react";

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    primaryColor: '#10b981',
    primaryTextColor: '#fff',
    primaryBorderColor: '#10b981',
    lineColor: '#64748b',
    secondaryColor: '#3b82f6',
    tertiaryColor: '#1f2937',
    mainBkg: '#0f172a',
    nodeBorder: '#1e293b',
    clusterBkg: '#1e293b',
    clusterBorder: '#334155',
    defaultLinkColor: '#64748b',
    titleColor: '#e2e8f0',
    edgeLabelBackground: '#0f172a',
    actorBkg: '#1e293b',
    actorBorder: '#3b82f6',
    actorTextColor: '#e2e8f0',
    actorLineColor: '#3b82f6',
    signalColor: '#10b981',
    signalTextColor: '#e2e8f0',
    labelBoxBkgColor: '#1e293b',
    labelBoxBorderColor: '#10b981',
    loopTextColor: '#e2e8f0',
    noteBkgColor: '#1e293b',
    noteBorderColor: '#eab308',
    noteTextColor: '#e2e8f0'
  }
});

const MermaidDiagram = ({ chart }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.removeAttribute("data-processed");
      mermaid.render("mermaid-svg-" + Math.random().toString(36).slice(2, 11), chart).then((result) => {
        ref.current.innerHTML = result.svg;
      });
    }
  }, [chart]);

  return <div ref={ref} className="flex justify-center w-full" />;
};

const steps = [
  {
    id: "auth",
    title: "분석 요청 및 인증",
    icon: <Lock size={22} />,
    color: "#3b82f6",
    file: "main.py > /analyze",
    desc: "API 엔드포인트 진입 및 보안 검증",
    tech: ["FastAPI", "OAuth2"],
    details: {
      payload: { user_id: "EJ-pro", repo_url: "..." },
      actions: [
        "사용자 GitHub Personal Access Token(PAT) 유효성 검증",
        "분석 요청 파라미터(URL, Branch) 정규화",
        "Rate Limit 및 API 접근 권한 상태 체크"
      ]
    }
  },
  {
    id: "cache",
    title: "코드 업데이트 검사",
    icon: <Search size={22} />,
    color: "#0ea5e9",
    file: "main.py",
    desc: "코드 업데이트 이력 대조 및 캐싱 전략 결정",
    tech: ["PostgreSQL", "SHA-256"],
    details: {
      payload: { last_commit: "a1b2c3d...", is_updated: true },
      actions: [
        "GitHub API를 통한 최신 커밋 해시(SHA) 실시간 확인",
        "기존 데이터베이스와 비교하여 신규 분석 필요성 판단",
        "Force Update 요청 시 기존 데이터 무효화 처리"
      ]
    }
  },
  {
    id: "scan",
    title: "분석 대상 스캐닝",
    icon: <Binary size={22} />,
    color: "#22d3ee",
    file: "github_fetcher.py",
    desc: "프로젝트 구조 파악 및 필터링",
    tech: ["Recursive Tree", "Globs"],
    details: {
      payload: { total_files: 142, targets: 89 },
      actions: [
        "디렉토리 재귀 순회 및 전체 파일 트리 구성",
        "타겟 확장자(code, config, docs) 기반 분석 대상 선별",
        ".gitignore 및 불필요한 바이너리 파일 분석 제외"
      ]
    }
  },
  {
    id: "fetch",
    title: "스트리밍 데이터 수집",
    icon: <CloudDownload size={22} />,
    color: "#2dd4bf",
    file: "github_fetcher.py",
    desc: "메모리 최적화 기반 파일 로드",
    tech: ["Python Generator", "Streaming"],
    details: {
      payload: "yield (path, content)",
      actions: [
        "Generator 패턴을 활용하여 대량의 파일을 순차적 로드",
        "파일별 Base64 페이로드 비동기 디코딩 처리",
        "대규모 레포지토리 로드시 메모리 부족(OOM) 방지"
      ]
    }
  },
  {
    id: "chunk",
    title: "텍스트 청크 분할",
    icon: <Scissors size={22} />,
    color: "#10b981",
    file: "core/rag/engine.py",
    desc: "대규모 코드를 의미 있는 단위로 분할",
    tech: ["RecursiveCharacterTextSplitter"],
    details: {
      payload: { chunk_size: 1000, overlap: 100 },
      actions: [
        "클래스, 함수 정의부 단위로 코드 블록을 논리적으로 분할",
        "문맥 유지를 위해 인접 청크 간 오버랩 구간 설정",
        "코드 가독성을 고려한 특수 구분자(Separators) 기반 분할"
      ]
    }
  },
  {
    id: "embed",
    title: "고차원 벡터 임베딩",
    icon: <Fingerprint size={22} />,
    color: "#84cc16",
    file: "core/rag/engine.py",
    desc: "코드를 수학적 벡터 공간으로 변환",
    tech: ["OpenAI Embeddings", "text-embedding-3-small"],
    details: {
      payload: { dimensions: 1536, model: "ada-002" },
      actions: [
        "분할된 코드 텍스트를 고차원 숫자 배열(Vector)로 수치화",
        "코드의 의미론적(Semantic) 특징을 고도로 함축된 데이터로 보존",
        "비슷한 기능을 하는 코드가 벡터 공간에서 가깝게 위치하도록 학습"
      ]
    }
  },
  {
    id: "indexing",
    title: "벡터 스토어 인덱싱",
    icon: <Database size={22} />,
    color: "#eab308",
    file: "database/vector_store.py",
    desc: "검색 최적화 기반 데이터 저장",
    tech: ["ChromaDB", "Elasticsearch"],
    details: {
      payload: { index_name: "code_idx", store: "in_memory" },
      actions: [
        "생성된 임베딩 벡터를 고속 검색 엔진에 저장 및 색인",
        "메타데이터(경로, 언어, 라인)와 벡터 데이터의 1:1 매핑",
        "HNSW 알고리즘 등을 활용한 대규모 벡터 공간 검색 최적화"
      ]
    }
  },
  {
    id: "retrieval",
    title: "유사도 기반 검색",
    icon: <Search size={22} />,
    color: "#f97316",
    file: "core/rag/retriever.py",
    desc: "질문과 가장 유사한 코드 조각 추출",
    tech: ["Cosine Similarity", "MMR"],
    details: {
      payload: { top_k: 12, score_threshold: 0.8 },
      actions: [
        "사용자 질문을 임베딩하여 벡터 공간에서의 거리 계산",
        "코사인 유사도 기반의 근접 이웃(K-Nearest Neighbors) 검색",
        "다양성 확보를 위한 MMR(Maximal Marginal Relevance) 필터링"
      ]
    }
  },
  {
    id: "ranking",
    title: "메타데이터 리랭킹",
    icon: <BarChart3 size={22} />,
    color: "#ef4444",
    file: "core/rag/engine.py",
    desc: "검색 결과의 순위 및 우선순위 조정",
    tech: ["Re-ranking", "Context Filtering"],
    details: {
      payload: { sorted_by: "relevance", limit: 8 },
      actions: [
        "파일 경로 가중치 및 코드 중요도를 기반으로 검색 결과 재정렬",
        "토큰 예산(Budget) 범위 내에서 최적의 컨텍스트 조합 선택",
        "README 등 가이드 문서와 실제 소스 코드의 비중 밸런싱"
      ]
    }
  },
  {
    id: "inference",
    title: "지능형 응답 생성",
    icon: <Cpu size={22} />,
    color: "#ec4899",
    file: "core/rag/engine.py",
    desc: "최종 아키텍처 기반 답변 도출",
    tech: ["LLM", "RAG Prompting"],
    details: {
      payload: { model: "gpt-4o-mini", stream: true },
      actions: [
        "정제된 코드 컨텍스트를 LLM 프롬프트에 동적 주입",
        "아키텍처 인과관계를 고려한 논리적인 기술 답변 생성",
        "사용자 질문에 최적화된 마크다운 기반 최종 응답 스트리밍"
      ]
    }
  }
];

const agentSteps = [
  {
    id: "analyzer",
    title: "🔍 분석가 에이전트 (Analyzer)",
    desc: "프로젝트 구조 및 비즈니스 로직 스캔",
    detail: "유저가 입력한 GitHub URL과 RAG(Retrieval-Augmented Generation)를 통해 프로젝트의 전체적인 기술 스택, 핵심 디렉토리, DB 스키마 등을 파악하여 요약 리포트를 생성합니다.",
    tip: "Spring Boot, React, FastAPI 등 프로젝트의 '정체성'을 확립하는 단계입니다."
  },
  {
    id: "router",
    title: "🔀 라우터 (Router)",
    desc: "분석 결과 기반의 동적 분기 처리",
    detail: "분석 리포트의 아키타입(BE/FE/ML 등)에 따라 적합한 Draft Writer에게 일을 넘깁니다. 기술 스택에 최적화된 프롬프트 템플릿을 동적으로 선택합니다.",
    tip: "백엔드면 API 명세 중심, 프론트엔드면 UI/UX 시작 가이드 중심으로 전략을 변경합니다."
  },
  {
    id: "writer",
    title: "✍️ 작성자 에이전트 (Draft Writer)",
    desc: "Markdown 기반 초안 파일 작성",
    detail: "라우터가 정해준 전략과 분석가의 리포트를 결합하여 README.md 초안을 작성합니다. 설치 방법, 기술 스택 뱃지, 주요 기능, 폴더 구조 등을 형상화합니다.",
    tip: "마크다운 문법의 가독성을 극대화하여 전문적인 느낌을 줍니다."
  },
  {
    id: "reviewer",
    title: "🕵️ 리뷰어 에이전트 (Critic / Reviewer)",
    desc: "마크다운 품질 검토 및 루프 제어",
    detail: "작성자의 결과물을 깐깐하게 검토합니다. 실행 명령어가 정확한지, 필수 항목이 누락되었는지 확인하여 부족할 경우 피드백을 담아 다시 작성자에게 돌려보냅니다.",
    tip: "LangGraph의 핵심인 '반복(Loop)'을 통해 수동 수정이 필요 없는 최종본을 보장합니다."
  }
];

const sequenceChart = `
sequenceDiagram
    autonumber
    participant U as User
    participant B as Backend (FastAPI)
    participant G as GitHub API
    participant V as Vector Engine (Chroma/OpenAI)
    participant DB as Vector Store
    participant AI as AI Assistant

    rect rgb(30, 41, 59)
    Note over U, AI: 1. 데이터 수집 및 전처리
    U->>B: 분석 요청 (Repo URL)
    B->>G: 코드 데이터 스트리밍 수집
    G-->>B: 원본 소스 코드 (Generator)
    B->>V: 텍스트 청크 분할 (Chunking)
    end
    
    rect rgb(15, 23, 42)
    Note over V, DB: 2. 벡터화 및 인덱싱
    V->>V: 고차원 임베딩 생성 (Embedding)
    V->>DB: 벡터 및 메타데이터 저장 (Upsert)
    DB-->>V: 인덱싱 완료
    end

    rect rgb(15, 23, 42)
    Note over U, AI: 3. 지능형 검색 및 응답
    U->>B: 사용자 질문 입력
    B->>V: 질문 벡터 변환
    V->>DB: 유사도 검색 (Similarity Search)
    DB-->>V: 최적의 코드 컨텍스트 반환
    V->>AI: 컨텍스트 주입 및 답변 요청
    AI-->>U: 최종 기술 답변 (Streaming)
    end
  `;

const dashboardChart = `
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend (Dashboard)
    participant B as Backend (FastAPI)
    participant R as RAG Engine (Vector/Elastic)
    participant AI as Intelligence (LLM)

    rect rgb(30, 41, 59)
    Note over U, AI: 1. 유저 질문 및 의도 분석
    U->>F: 질문 입력 (예: "로그인 기능과 DB 연결 방식 알려줘")
    F->>B: POST /chat (payload: question)
    B->>AI: 질문 기반 키워드 및 의도 추출
    AI-->>B: 추출 키워드: ["Login", "Database", "ORM"]
    end

    rect rgb(15, 23, 42)
    Note over B, R: 2. 지능형 컨텍스트 검색
    B->>R: 키워드 간 상관관계 기반 하이브리드 검색
    R-->>B: 관련 코드 조각 및 아키텍처 메타데이터
    end

    rect rgb(15, 23, 42)
    Note over B, AI: 3. 응답 생성 및 상관관계 도출
    B->>AI: 검색된 컨텍스트 + 키워드 상관관계 분석 요청
    Note right of AI: 아키텍처 노드와의 매핑 및 기술적 인과관계 분석
    AI-->>B: 심층 분석 답변 (Markdown)
    end

    B-->>F: 최종 응답 스트리밍
    F-->>U: 답변 표시 및 관련 코드/아키텍처 하이라이트
  `;

export default function DocDeepPipeline() {
  const [activeNode, setActiveNode] = useState(0);
  const [viewType, setViewType] = useState("pipeline"); // "pipeline", "agent", "sequence", or "dashboard"

  const active = steps[activeNode];

  return (
    <div className="min-h-screen bg-[#030712] text-[#e2e8f0] p-8 flex flex-col items-center" style={{ fontFamily: "Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif" }}>
      {/* Header Area */}
      <div className="w-full max-w-6xl mb-12 text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-800/50 border border-slate-700 rounded-full text-xs text-emerald-400 font-bold uppercase tracking-widest mb-4">
            <Database size={14} /> 아키텍처 심층 분석 (Architecture Deep Dive)
          </div>
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white mb-2 leading-tight">
            Doc<span className="text-emerald-400">DeepPipeline</span>
          </h1>
          <p className="text-slate-400 text-lg">내부 데이터 실행 흐름 및 10단계 핵심 파이프라인 가이드</p>
        </div>
        
        <div className="flex flex-col gap-6">
          {/* View Toggle */}
          <div className="flex bg-slate-900/50 p-1 rounded-2xl border border-slate-800 self-center md:self-end">
            <button 
              onClick={() => setViewType("pipeline")}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${viewType === "pipeline" ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-slate-300"}`}
            >
              Main Pipeline
            </button>
            <button 
              onClick={() => setViewType("agent")}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${viewType === "agent" ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-slate-300"}`}
            >
              README Agent
            </button>
            <button 
              onClick={() => setViewType("sequence")}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${viewType === "sequence" ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-slate-300"}`}
            >
              Analysis
            </button>
            <button 
              onClick={() => setViewType("dashboard")}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${viewType === "dashboard" ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-slate-300"}`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => setViewType("intelligence")}
              className={`px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${viewType === "intelligence" ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20" : "text-slate-500 hover:text-slate-300"}`}
            >
              AI Decision
            </button>
          </div>

          <div className="flex gap-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
              <div className="text-[11px] text-slate-500 mb-1 font-bold tracking-wider uppercase">
                {viewType === "pipeline" ? "분석 단계" : viewType === "agent" ? "에이전트 수" : viewType === "sequence" ? "핵심 모듈" : viewType === "dashboard" ? "RAG Flow" : "판단 포인트"}
              </div>
              <div className="text-2xl font-black text-slate-100">
                {viewType === "pipeline" ? "10 Steps" : viewType === "agent" ? "4 Agents" : viewType === "sequence" ? "6 Modules" : viewType === "dashboard" ? "RAG Flow" : "5 Points"}
              </div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
              <div className="text-[11px] text-slate-500 mb-1 font-bold tracking-wider uppercase">엔진 상태</div>
              <div className="text-2xl font-black text-emerald-400 animate-pulse">READY</div>
            </div>
          </div>
        </div>
      </div>

      {viewType === "pipeline" ? (
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-5 relative flex flex-col gap-3">
            <div className="absolute left-7 top-10 bottom-10 w-[2px] bg-slate-800/50 z-0"></div>
            {steps.map((step, idx) => (
              <div key={step.id} className="relative z-10 flex gap-5 cursor-pointer group" onClick={() => setActiveNode(idx)}>
                <div className="flex flex-col items-center mt-1">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-xl ${activeNode === idx ? 'scale-110 ring-4 ring-offset-4 ring-offset-[#030712] ring-opacity-20 border-2' : 'bg-slate-900/80 border border-slate-800 opacity-50 group-hover:opacity-100 group-hover:bg-slate-800'}`} style={{ backgroundColor: activeNode === idx ? `${step.color}20` : '', borderColor: activeNode === idx ? step.color : '', color: activeNode === idx ? step.color : '#64748b', boxShadow: activeNode === idx ? `0 0 30px ${step.color}30` : '', ringColor: activeNode === idx ? step.color : 'transparent' }}>
                    {step.icon}
                  </div>
                  {idx < steps.length - 1 && <div className={`w-[2px] h-full my-1 transition-colors ${activeNode >= idx ? 'bg-emerald-500/40' : 'bg-slate-800'}`}></div>}
                </div>
                <div className={`flex-1 p-4 rounded-2xl border transition-all duration-300 ${activeNode === idx ? 'bg-slate-900 border-slate-700 shadow-2xl translate-x-1' : 'bg-transparent border-transparent opacity-50 group-hover:opacity-100 group-hover:translate-x-1'}`}>
                  <div className="text-[11px] font-black tracking-widest mb-1 uppercase" style={{ color: step.color }}>Step 0{idx + 1}</div>
                  <div className={`font-bold text-lg ${activeNode === idx ? 'text-white' : 'text-slate-400'}`}>{step.title}</div>
                </div>
              </div>
            ))}
          </div>
          <div className="lg:col-span-7">
            <div className="sticky top-8 bg-slate-900/60 backdrop-blur-2xl border border-slate-800 rounded-[2.5rem] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative overflow-hidden h-full min-h-[650px] flex flex-col">
              <div className="absolute -top-24 -right-24 w-96 h-96 blur-[120px] rounded-full opacity-30 pointer-events-none transition-colors duration-1000" style={{ backgroundColor: active.color }}></div>
              <div className="relative z-10 border-b border-slate-800 pb-8 mb-8">
                <div className="flex items-center gap-5 mb-3">
                  <div className="p-3 rounded-2xl bg-black border border-slate-800 shadow-inner" style={{ color: active.color }}>{active.icon}</div>
                  <div>
                    <h2 className="text-3xl font-black text-white tracking-tight">{active.title}</h2>
                    <p className="text-slate-400 text-base mt-2 font-medium">{active.desc}</p>
                  </div>
                </div>
              </div>
              <div className="relative z-10 flex-1 flex flex-col gap-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                    <div className="text-[11px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2"><Terminal size={14} /> 실행 파일 (Source)</div>
                    <div className="font-bold text-emerald-400 text-sm font-mono break-all leading-relaxed">{active.file}</div>
                  </div>
                  <div className="bg-black/40 rounded-2xl p-5 border border-slate-800/80 shadow-md">
                    <div className="text-[11px] text-slate-500 mb-3 tracking-widest font-black uppercase flex items-center gap-2"><Layers size={14} /> 핵심 기술 (Core Tech)</div>
                    <div className="flex flex-wrap gap-2">{active.tech.map(t => <span key={t} className="px-3 py-1 bg-slate-800/80 rounded-lg text-[11px] font-bold shadow-sm" style={{ color: active.color }}>{t}</span>)}</div>
                  </div>
                </div>
                <div className="flex-1 bg-black/40 rounded-3xl border border-slate-800/80 p-8 mt-2 flex flex-col shadow-2xl ring-1 ring-white/5">
                  <div className="text-[11px] text-slate-500 mb-6 tracking-widest font-black uppercase flex items-center gap-2"><Info size={16} /> 상세 동작 로직 (Internal Logic)</div>
                  <div className="space-y-5 mb-10">{active.details.actions.map((act, i) => <div key={i} className="flex items-start gap-4 text-[15px] text-slate-200 leading-relaxed font-medium"><CheckCircle2 size={18} className="mt-1 shrink-0" style={{ color: active.color }} /><span>{act}</span></div>)}</div>
                  <div className="mt-auto pt-8 border-t border-slate-800">
                    <div className="text-[11px] text-slate-500 mb-4 tracking-widest font-black uppercase flex items-center justify-between"><span>데이터 구조 (Data Shape)</span><span className="text-emerald-500/70 bg-emerald-500/10 px-2 py-0.5 rounded text-[9px]">LIVE_INSTANCE</span></div>
                    <pre className="bg-black/80 border border-slate-800 p-6 rounded-2xl text-[12px] overflow-x-auto text-pink-400 font-mono shadow-inner leading-relaxed custom-scrollbar max-h-[180px]"><code>{JSON.stringify(active.details.payload, null, 2)}</code></pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : viewType === "agent" ? (
        <div className="w-full max-w-6xl space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 relative">
            <div className="hidden lg:block absolute top-[40px] left-[15%] right-[15%] h-[2px] bg-slate-800 z-0"></div>
            {agentSteps.map((agent, idx) => (
              <div key={agent.id} className="relative z-10 glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-emerald-500/30 transition-all group">
                <div className="w-16 h-16 rounded-2xl bg-black border border-slate-800 flex items-center justify-center mb-6 text-emerald-400 group-hover:scale-110 transition-transform"><span className="text-2xl">{idx + 1}</span></div>
                <h3 className="text-xl font-bold text-white mb-3 tracking-tight">{agent.title}</h3>
                <p className="text-emerald-500/80 text-sm font-bold mb-4">{agent.desc}</p>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">{agent.detail}</p>
                <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
                  <div className="text-[10px] text-emerald-500 font-black uppercase tracking-widest mb-1 flex items-center gap-1"><Info size={12} /> Insight</div>
                  <p className="text-xs text-slate-300 italic">"{agent.tip}"</p>
                </div>
                {idx === 3 && <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-4 py-1.5 rounded-full text-[11px] font-black animate-bounce"><RefreshCw size={12} /> CONDITIONAL LOOP BACK TO WRITER</div>}
              </div>
            ))}
          </div>
          <div className="mt-20 glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 blur-[80px] rounded-full"></div>
            <div className="relative z-10">
              <h2 className="text-3xl font-black text-white mb-8 tracking-tighter flex items-center gap-3"><CheckCircle2 className="text-emerald-500" />최종본 출력 (Final Output)</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
                <div className="space-y-6">
                  <p className="text-slate-300 text-lg leading-relaxed">리뷰어 에이전트의 승인을 받은 완벽한 <b>README.md</b>가 사용자에게 제공됩니다. 단순한 코드 나열이 아닌 프로젝트의 핵심 가치와 아키텍처를 전문적으로 설명하는 고품질 문서를 경험하세요.</p>
                  <ul className="space-y-3">{["사용자 맞춤형 섹션 자동 구성", "프로젝트 핵심 기능(Feature) 도출", "정확한 설치 및 실행 가이드", "세련된 기술 스택 뱃지 자동 삽입"].map(item => <li key={item} className="flex items-center gap-3 text-slate-400 text-sm font-medium"><ArrowRight size={14} className="text-emerald-500" />{item}</li>)}</ul>
                </div>
                <div className="bg-black/40 rounded-3xl p-8 border border-white/5 font-mono text-[13px] text-pink-400/90 whitespace-pre-wrap leading-relaxed shadow-inner"># 🚀 AwesomeProject{"\\n"}- "개발자를 위한 최고의 생산성 도구"{"\\n\\n"}## ✨ 주요 기능{"\\n"}- ⚡ **실시간 동기화**: WebSocket 기반...{"\\n"}- 🔒 **안전한 인증**: JWT 기반 Oauth...{"\\n\\n"}## 📂 폴더 구조{"\\n"}📦 src/{"\\n"} ┣ 📂 components{"\\n"} ┗ 📂 utils</div>
              </div>
            </div>
          </div>
        </div>
      ) : viewType === "sequence" ? (
        <div className="w-full max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500/50 to-blue-500/50"></div>
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-12">
                <div>
                  <h2 className="text-3xl font-black text-white mb-2 tracking-tighter flex items-center gap-3"><RefreshCw className="text-emerald-500" />전체 시스템 시퀀스 (Full System Sequence)</h2>
                  <p className="text-slate-400 text-sm">사용자 요청부터 최종 결과물 출력까지의 시간순 실행 흐름</p>
                </div>
                <div className="flex items-center gap-3 bg-black/40 px-4 py-2 rounded-xl border border-white/5"><div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div><span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">Live Flow Logic</span></div>
              </div>
              <div className="bg-slate-950/80 rounded-3xl p-8 border border-white/5 shadow-2xl overflow-x-auto custom-scrollbar"><MermaidDiagram chart={sequenceChart} /></div>
              <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5"><h4 className="text-emerald-400 font-bold mb-2 flex items-center gap-2"><Search size={16} /> 캐싱 최적화</h4><p className="text-xs text-slate-400 leading-relaxed">동일한 커밋 SHA에 대해서는 파싱 과정을 생략하고 즉시 응답하여 서버 리소스를 보존합니다.</p></div>
                <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5"><h4 className="text-blue-400 font-bold mb-2 flex items-center gap-2"><Cpu size={16} /> 스트리밍 분석</h4><p className="text-xs text-slate-400 leading-relaxed">대규모 레포지토리도 Generator 패턴을 통해 메모리 부하 없이 실시간으로 파싱합니다.</p></div>
                <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5"><h4 className="text-purple-400 font-bold mb-2 flex items-center gap-2"><Sparkles size={16} /> 에이전트 협업</h4><p className="text-xs text-slate-400 leading-relaxed">단순 LLM 호출이 아닌, 4가지 전문 에이전트의 상호 검토 과정을 거쳐 품질을 보장합니다.</p></div>
              </div>
            </div>
          </div>
        </div>
      ) : viewType === "dashboard" ? (
        <div className="w-full max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="glass-panel bg-slate-900/60 border border-slate-800 rounded-[2.5rem] p-12 overflow-hidden relative">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500/50 to-purple-500/50"></div>
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-12">
                <div>
                  <h2 className="text-3xl font-black text-white mb-2 tracking-tighter flex items-center gap-3"><MessageSquare className="text-blue-500" />대시보드 지능형 질의 흐름 (Dashboard RAG Flow)</h2>
                  <p className="text-slate-400 text-sm">사용자 질문에 대한 의도 파악 및 아키텍처 기반 심층 답변 생성 과정</p>
                </div>
                <div className="flex items-center gap-3 bg-black/40 px-4 py-2 rounded-xl border border-white/5"><div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div><span className="text-[10px] text-slate-400 font-black uppercase tracking-widest">RAG Intelligence</span></div>
              </div>
              <div className="bg-slate-950/80 rounded-3xl p-8 border border-white/5 shadow-2xl overflow-x-auto custom-scrollbar"><MermaidDiagram chart={dashboardChart} /></div>
              <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5"><h4 className="text-blue-400 font-bold mb-2 flex items-center gap-2"><Search size={16} /> 의도 기반 키워드</h4><p className="text-xs text-slate-400 leading-relaxed">단순 키워드 매칭을 넘어 LLM을 통해 질문의 기술적 의도를 파악하고 핵심 키워드 간의 상관관계를 분석합니다.</p></div>
                <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
                  <h4 className="text-purple-400 font-bold mb-2 flex items-center gap-2">
                    <Layers size={16} /> 지능형 컨텍스트 검색
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    <b>구현:</b> <code className="text-purple-300">similarity_search</code>를 통한 벡터 검색 후, <code className="text-purple-300">networkx</code> 그래프의 이웃 노드(<code className="text-purple-300">neighbors</code>)를 추적하여 관련 의존성 파일을 함께 수집합니다.
                  </p>
                </div>
                <div className="p-6 bg-slate-900/40 rounded-2xl border border-white/5">
                  <h4 className="text-emerald-400 font-bold mb-2 flex items-center gap-2">
                    <Sparkles size={16} /> 응답 생성 및 상관관계 도출
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    <b>구현:</b> 수집된 코드 청크와 그래프 추적 데이터를 <code className="text-emerald-300">SystemPrompt</code>에 주입하며, <b>Code-First Analysis</b> 전략을 통해 문서보다 실제 소스 코드의 로직을 우선하여 답변을 생성합니다.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="w-full max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Logic 1: Intent Judgment */}
            <div className="glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-blue-500/30 transition-all">
              <div className="flex items-start gap-5">
                <div className="p-4 rounded-2xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <MessageSquare size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">질문 의도 및 키워드 추출</h3>
                  <p className="text-sm text-slate-400 leading-relaxed mb-4">
                    사용자의 자연어 질문에서 <b>기술적 의도</b>를 파악합니다. 단순히 단어를 찾는 것이 아니라, "로그인"이라는 단어에서 "Security", "Auth", "JWT"와 같은 아키텍처 키워드를 스스로 연상하여 검색 범위를 결정합니다.
                  </p>
                  <div className="bg-black/40 px-4 py-2 rounded-xl text-[11px] font-mono text-blue-300">
                    judgment_logic: extract_technical_intent(query)
                  </div>
                </div>
              </div>
            </div>

            {/* Logic 2: Tech Identity Judgment */}
            <div className="glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-emerald-500/30 transition-all">
              <div className="flex items-start gap-5">
                <div className="p-4 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Brain size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">프로젝트 정체성 확립</h3>
                  <p className="text-sm text-slate-400 leading-relaxed mb-4">
                    수집된 파일 구조와 코드 일부를 보고 "이 프로젝트는 Spring Boot 기반의 MSA 아키텍처다"라는 <b>기술적 결론</b>을 내립니다. 이 판단에 따라 이후 문서화의 톤앤매너와 핵심 설명 부위가 결정됩니다.
                  </p>
                  <div className="bg-black/40 px-4 py-2 rounded-xl text-[11px] font-mono text-emerald-300">
                    judgment_logic: determine_project_archetype(files)
                  </div>
                </div>
              </div>
            </div>

            {/* Logic 3: Dynamic Routing */}
            <div className="glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-purple-500/30 transition-all">
              <div className="flex items-start gap-5">
                <div className="p-4 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Share2 size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">워크플로우 동적 분기</h3>
                  <p className="text-sm text-slate-400 leading-relaxed mb-4">
                    분석된 아키타입에 따라 <b>어떤 에이전트에게 업무를 배정할지</b> 판단합니다. 백엔드 중심이면 API 설계자로, 프론트엔드 중심이면 UI/UX 분석가로 작업을 라우팅하여 전문성을 확보합니다.
                  </p>
                  <div className="bg-black/40 px-4 py-2 rounded-xl text-[11px] font-mono text-purple-300">
                    judgment_logic: route_to_specialized_agent(report)
                  </div>
                </div>
              </div>
            </div>

            {/* Logic 4: Quality Review & Loop */}
            <div className="glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-orange-500/30 transition-all">
              <div className="flex items-start gap-5">
                <div className="p-4 rounded-2xl bg-orange-500/10 text-orange-400 border border-orange-500/20">
                  <ShieldCheck size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">품질 검토 및 루프 제어</h3>
                  <p className="text-sm text-slate-400 leading-relaxed mb-4">
                    생성된 결과물이 설정된 기준(Accuracy, Clarity, Detail)을 충족하는지 <b>비판적으로 평가</b>합니다. 기준 미달 시 "재작성" 판단을 내려 에이전트 루프를 다시 돌리는 의사결정을 수행합니다.
                  </p>
                  <div className="bg-black/40 px-4 py-2 rounded-xl text-[11px] font-mono text-orange-300">
                    judgment_logic: evaluate_and_loop_back(content)
                  </div>
                </div>
              </div>
            </div>

            {/* Logic 5: Causality Inference */}
            <div className="glass-panel bg-slate-900/40 border border-slate-800 rounded-3xl p-8 hover:border-pink-500/30 transition-all col-span-1 md:col-span-2">
              <div className="flex items-start gap-5">
                <div className="p-4 rounded-2xl bg-pink-500/10 text-pink-400 border border-pink-500/20">
                  <Bot size={24} />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">아키텍처 인과관계 추론</h3>
                  <p className="text-sm text-slate-400 leading-relaxed mb-4">
                    단편적인 코드 조각들을 모아 <b>전체적인 실행 흐름(Data Flow)을 추론</b>합니다. A 파일의 변경이 B 모듈에 어떤 영향을 줄지, 기술적 인과관계를 스스로 판단하여 사용자에게 인사이트를 제공합니다.
                  </p>
                  <div className="bg-black/40 px-4 py-2 rounded-xl text-[11px] font-mono text-pink-300">
                    judgment_logic: infer_architectural_causality(contexts)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
