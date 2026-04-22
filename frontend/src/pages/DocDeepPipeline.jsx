import React, { useState } from "react";
import { 
  Database, Github, Braces, Layers, Link2, 
  Cpu, FileCode2, Code, ArrowRight, Share2, Info, CheckCircle2,
  Lock, Search, CloudDownload, Terminal, BarChart3, Binary
} from "lucide-react";

export default function DocDeepPipeline() {
  const [activeNode, setActiveNode] = useState(0);

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
      id: "factory",
      title: "파서 팩토리 라우팅",
      icon: <Terminal size={22} />,
      color: "#10b981",
      file: "core/parser/factory.py",
      desc: "언어별 최적화 분석기 할당",
      tech: ["Factory Pattern"],
      details: {
        payload: "get_parser_result(ext)",
        actions: [
          "입력 파일의 확장자 분석 후 언어 전용 파서 매칭",
          "멀티 언어 프로젝트(Polyglot) 동시 분석 지원",
          "알 수 없는 형식의 경우 기본 메타데이터 추출기로 폴백"
        ]
      }
    },
    {
      id: "parse",
      title: "AST 심층 구문 분석",
      icon: <FileCode2 size={22} />,
      color: "#84cc16",
      file: "core/parser/lang/*.py",
      desc: "Native AST 및 Regex 엔진 기반 구조 추출",
      tech: ["Native AST (Python)", "Regex Engine (JS/JAVA/KT)"],
      details: {
        payload: { classes: ["Auth"], functions: ["login"] },
        actions: [
          "Python 내장 ast 모듈 및 언어별 정규표현식 엔진을 활용한 고속 메타데이터 추출",
          "클래스, 함수, 네임스페이스 및 Import 구문의 정확한 식별 및 정규화",
          "도커 컨테이너 환경에서의 OS 종속성 제거 및 런타임 안정성 확보"
        ]
      }
    },
    {
      id: "persistence",
      title: "데이터 영구 저장",
      icon: <Database size={22} />,
      color: "#eab308",
      file: "database/models.py",
      desc: "분석 정보의 DB 정규화 저장",
      tech: ["SQLAlchemy", "PostgreSQL"],
      details: {
        payload: { status: "commit_success", rows: 124 },
        actions: [
          "파싱된 정보와 원본 코드를 PostgreSQL 트랜잭션 저장",
          "파일별 라인 수, 키워드, 메타데이터 JSON 필드화",
          "프로젝트 레코드 업데이트 및 분석 시간 기록"
        ]
      }
    },
    {
      id: "graph",
      title: "의존성 네트워크 구축",
      icon: <Share2 size={22} />,
      color: "#f97316",
      file: "core/graph/graph_builder.py",
      desc: "Resolver Factory 기반 상호 참조 관계 정립",
      tech: ["Resolver Factory", "Language Resolvers", "NetworkX"],
      details: {
        payload: "nx.DiGraph(nodes=89, edges=234)",
        actions: [
          "ResolverFactory를 통한 언어별 맞춤형 리졸버(PythonResolver, JSResolver 등) 배정",
          "Import 구문의 점 표기법, 상대 경로 등을 실제 파일 시스템 경로로 정규화 매핑",
          "NetworkX DiGraph 기반의 전역 모듈 의존성 네트워크 및 토폴로지 구성"
        ]
      }
    },
    {
      id: "metrics",
      title: "네트워크 통계 분석",
      icon: <BarChart3 size={22} />,
      color: "#ef4444",
      file: "main.py / graph_builder",
      desc: "아키텍처 시각화 데이터 가공",
      tech: ["Graph Algorithm", "JSON"],
      details: {
        payload: { degree_dict: { "main.py": 12 } },
        actions: [
          "노드별 연결 지수(Degree) 계산을 통한 중심 파일 식별",
          "프론트엔드 시각화(D3.js/3D-Force)를 위한 JSON 변환",
          "프로젝트 아키텍처 토폴로지 데이터 생성"
        ]
      }
    },
    {
      id: "engine",
      title: "RAG 엔진 및 세션 활성화",
      icon: <Cpu size={22} />,
      color: "#ec4899",
      file: "engine.py",
      desc: "LLM 대화 준비 및 엔진 로드",
      tech: ["LangChain", "Vector Store"],
      details: {
        payload: "ChatFolioEngine.ask()_ready",
        actions: [
          "분석된 전체 데이터를 ChatFolioEngine 컨텍스트에 로드",
          "벡터 임베딩 및 검색 증강 생성(RAG) 파이프라인 구성",
          "사용자와의 상호작용을 위한 채팅 세션 오픈"
        ]
      }
    }
  ];

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
        
        <div className="flex gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
            <div className="text-[11px] text-slate-500 mb-1 font-bold tracking-wider uppercase">분석 단계</div>
            <div className="text-2xl font-black text-slate-100">10 Steps</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 min-w-[140px] shadow-lg">
            <div className="text-[11px] text-slate-500 mb-1 font-bold tracking-wider uppercase">엔진 상태</div>
            <div className="text-2xl font-black text-emerald-400 animate-pulse">READY</div>
          </div>
        </div>
      </div>

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
    </div>
  );
}
