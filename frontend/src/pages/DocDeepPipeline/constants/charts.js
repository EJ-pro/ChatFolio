export const sequenceChart = `
sequenceDiagram
    autonumber
    participant U as User
    participant B as Backend (FastAPI)
    participant G as GitHub API
    participant P as Parser Engine
    participant DB as PostgreSQL
    participant AI as AI Agent (LangGraph)

    rect rgb(30, 41, 59)
    Note over U, AI: 1. 분석 요청 및 캐시 확인
    U->>B: 분석 요청 (Repo URL)
    B->>G: 최신 커밋 SHA 조회
    G-->>B: SHA 응답
    B->>DB: 캐시 존재 여부 확인 (SHA 매칭)
    end
    
    alt 캐시 히트 (Cache Hit)
        DB-->>B: 기존 분석 데이터 반환
        B-->>U: 분석 결과 즉시 표시
    else 캐시 미스 (Cache Miss)
        rect rgb(15, 23, 42)
        Note over B, P: 2. 코드 스캔 및 심층 분석
        B->>G: 레포지토리 구조 스캔
        G-->>B: 파일 트리 데이터
        B->>P: 멀티 언어 파싱 시작
        loop 모든 파일 대상
            P->>P: AST 및 정규표현식 메타데이터 추출
        end
        P->>DB: 메타데이터 및 의존성 그래프 저장
        end

        rect rgb(15, 23, 42)
        Note over B, AI: 3. 문서 생성 에이전트 가동
        B->>AI: 문서 생성 워크플로우 트리거
        Note right of AI: Analyzer -> Router -> Writer -> Reviewer
        AI->>AI: 지능형 루프를 통한 품질 최적화
        AI-->>B: 최종 README.md 결과물
        end
        
        B-->>U: 분석 완료 및 문서 제공
    end
  `;

export const dashboardChart = `
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
