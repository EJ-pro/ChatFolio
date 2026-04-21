# ChatFolio Backend Documentation

ChatFolio의 백엔드는 FastAPI를 기반으로 하며, GitHub 레포지토리 분석, 의존성 그래프 구축, 그리고 RAG(Retrieval-Augmented Generation) 기반의 AI 챗봇 기능을 제공합니다.

## 📂 프로젝트 구조 (Directory Structure)

```text
backend/
├── main.py                # 시스템의 진입점 및 API 엔드포인트 정의
├── api/
│   └── auth.py            # GitHub OAuth 및 JWT 인증 로직
├── core/
│   ├── parser/            # 코드 수집 및 구문 분석
│   │   ├── github_fetcher.py   # GitHub API 연동 (파일 스트리밍 및 메타데이터 추출)
│   │   └── kotlin_parser.py    # Kotlin 코드 분석 (클래스/함수/의존성 추출)
│   ├── graph/             # 아키텍처 분석 기반
│   │   └── graph_builder.py    # 분석된 데이터를 기반으로 의존성 그래프 구축
│   └── rag/               # AI 및 챗봇 엔진
│       └── engine.py           # ChatFolioEngine (RAG 로직, Mermaid 생성, README 생성)
├── database/              # 데이터 영속성 계층
│   ├── database.py        # SQLAlchemy 설정 및 DB 연결 세션 관리
│   └── models.py          # DB 스키마 정의 (User, Project, ChatSession 등)
├── models/
│   └── schemas.py         # Pydantic 기반의 API 요청/응답 스키마
└── requirements.txt       # 의존성 패키지 목록
```

---

## 🛠 주요 파일별 상세 설명

### 1. `main.py`
전체 시스템의 오케스트레이터입니다.
- **`/analyze`**: 레포지토리 URL을 받아 파일을 수집하고, 그래프를 생성하며 분석을 수행합니다. StreamingResponse를 통해 실시간 로그를 프론트로 전달합니다.
- **`/chat`**: 사용자의 질문에 대해 분석된 코드베이스와 그래프 정보를 바탕으로 답변을 생성합니다.
- **`/generate/*`**: Mermaid 아키텍처 다이어그램이나 README.md 생성을 요청합니다.

### 2. `core/parser/github_fetcher.py` (`GitHubFetcher`)
- GitHub API를 사용하여 특정 레포지토리의 소스코드를 수집합니다.
- 모든 파일을 한꺼번에 메모리에 올리지 않고 **Generator**를 사용하여 스트리밍 방식으로 처리하므로 대규모 프로젝트 분석 시 메모리 효율적입니다.

### 3. `core/parser/kotlin_parser.py`
- 코드 내부의 `import`, `class`, `function` 키워드를 추적하여 파일 간의 연결 관계를 파악합니다.
- 현재 Kotlin에 특화되어 있으나, 다른 언어 확장이 가능하도록 설계되어 있습니다.

### 4. `core/rag/engine.py` (`ChatFolioEngine`)
본 프로젝트의 핵심 두뇌 역할을 합니다.
- **RAG (Search)**:
    1. **Vector Search**: 사용자의 질문과 의미적으로 유사한 코드 조각을 `InMemoryVectorStore`에서 검색합니다.
    2. **Graph Search**: 검색된 핵심 파일의 의존성 그래프를 탐색하여, 해당 파일이 참조하거나 참조되는 상/하위 컨텍스트를 추가로 확보합니다.
- **Prompting**: 수집된 "코드 조각 + 그래프 정보"를 바탕으로 LLM(Groq/OpenAI)에게 전문적인 답변을 생성하도록 지시합니다.
- **Utility**: LLM을 활용하여 복잡한 코드를 정리된 Mermaid 다이어그램이나 고품질 README로 변환합니다.

### 5. `database/models.py`
- **User**: 사용자 정보 및 GitHub 토큰 관리.
- **Project**: 분석된 레포지토리 정보, 파일 본문, 그래프 데이터(JSON) 보관.
- **ChatSession/ChatMessage**: 대화 내역 및 참조된 소스 코드 정보(Sources) 저장.

---

## 🔄 주요 워크플로우

### 분석 프로세스 (Analysis)
1. 사용자가 GitHub URL 입력.
2. `GitHubFetcher`가 최신 커밋 확인 및 파일 수집 시작.
3. 수집된 각 파일에 대해 `kotlin_parser`가 메타데이터 추출.
4. `DependencyGraphBuilder`가 파일 간의 연결망(Graph) 완성.
5. 모든 정보 DB 저장 및 분석 완료 응답.

### 채팅 프로세스 (Chat)
1. 사용자가 질문 ("이 프로젝트의 로그인 로직은 어디에 있어?") 입력.
2. 시스템이 질문의 키워드로 **벡터 유사도 검색** 수행 → 가장 관련 있는 코드(예: `AuthService.kt`) 발견.
3. 검색된 파일의 **상위/하위 의존성**을 그래프에서 탐색 → 연결된 파일(예: `UserRepository.kt`, `LoginController.kt`)을 컨텍스트로 추가.
4. LLM이 최종 정보를 취합하여 "로그인 로직은 AuthService.kt에 정의되어 있으며 UserRepository.kt를 참조합니다..." 와 같은 답변 생성.

---

## 🚀 챗봇 구현 가이드 (참고용)
챗봇 기능을 커스텀하시려면 주로 `backend/core/rag/engine.py`를 수정하게 될 것입니다.
- 질문에 대한 답변 방식을 바꾸고 싶다면 `ask()` 메서드 내부의 프롬프트를 수정하세요.
- 검색 성능을 높이고 싶다면 `_prepare_vector_db()`의 청크 분할 방식이나 검색 로직을 튜닝하세요.
