import React from "react";
import { 
  Lock, Search, Binary, CloudDownload, Terminal, FileCode2, Database, Share2, BarChart3, Cpu 
} from "lucide-react";

export const steps = [
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

export const agentSteps = [
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
