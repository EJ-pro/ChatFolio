<div align="center">

```
            ██████╗██╗  ██╗ █████╗ ████████╗███████╗ ██████╗ ██╗     ██╗ ██████╗
            ██╔════╝██║  ██║██╔══██╗╚══██╔══╝██╔════╝██╔═══██╗██║     ██║██╔═══██╗
            ██║     ███████║███████║   ██║   █████╗  ██║   ██║██║     ██║██║   ██║
            ██║     ██╔══██║██╔══██║   ██║   ██╔══╝  ██║   ██║██║     ██║██║   ██║
            ╚██████╗██║  ██║██║  ██║   ██║   ██║     ╚██████╔╝███████╗██║╚██████╔╝
            ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝      ╚═════╝ ╚══════╝╚═╝ ╚═════╝
```

**AI 기반 지능형 레포지토리 분석 · 자동 문서화 플랫폼**

GitHub URL 하나로 코드 의존성을 시각화하고, AI와 대화하며, 고품질 README를 자동 생성합니다.

<br/>

[![Version](https://img.shields.io/badge/version-1.0.0-6366f1?style=for-the-badge)](https://github.com/EJ-pro/ChatFolio)
[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B6B?style=for-the-badge)](https://langchain-ai.github.io/langgraph)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

[**🚀 시작하기**](#-시작하기-getting-started) · [**✨ 주요 기능**](#-주요-기능) · [**⚙️ 핵심 아키텍처**](#%EF%B8%8F-핵심-아키텍처) · [**📂 폴더 구조**](#-폴더-구조)

</div>

---

## 💡 프로젝트 소개

새로운 오픈소스에 합류하거나 방대한 레거시 코드를 인계받을 때, 코드 파악에 드는 비용은 상상 이상입니다.

**ChatFolio**는 이 문제를 해결합니다. GitHub URL 하나만 입력하면:

- 📊 수천 개의 파일 간 **의존성 그래프**를 자동 추출
- 🤖 추출된 그래프를 기반으로 **AI 코드 챗봇**과 즉시 대화
- 📝 프로젝트 정체성을 분석해 **고품질 README**를 멀티 에이전트가 자동 작성

---

## 🚀 최근 업데이트 (v1.1.0)

- **🌐 글로벌 서비스 대응 (Multilingual Support)**: UI 전체 영문화를 완료하였으며, 이제 한국어와 영어로 분석 및 문서 생성이 가능합니다.
- **🚀 차세대 LLM 엔진 (Qwen 3.6 MoE)**: 35B 파라미터급 MoE(Mixture-of-Experts) 모델을 도입하여 에이전트 코딩 및 아키텍처 추론 능력을 극대화했습니다.
- **🎯 초정밀 하이브리드 RAG (BGE-M3 + BM25)**: 글로벌 1위급 임베딩 모델(BGE-M3)과 키워드 검색(BM25)을 결합하고, LLM 리랭킹을 거치는 3단계 검색 파이프라인을 구축했습니다.
- **🏗️ AI 아키텍처 분석**: 프로젝트의 의존성 그래프를 분석하여 디자인 패턴, 컴포넌트 역할, 데이터 흐름에 대한 전문적인 리포트를 자동 생성합니다.
- **⚡ 성능 최적화 (Caching Engine)**: 실시간 GitHub API 호출 의존도를 낮추고 DB 캐싱 레이어를 구축하여, 마이페이지 로딩 속도를 최대 10배 이상 개선했습니다.

---

## ✨ 주요 기능

<table>
  <tr>
    <td width="50%">
      <h3>🕸 아키텍처 시각화</h3>
      <p><code>NetworkX</code>로 분석된 파일 간 의존성을 물리 시뮬레이션 기반 <code>react-force-graph</code>로 인터랙티브하게 렌더링합니다. 노드 크기로 핵심 파일을 즉시 파악할 수 있습니다.</p>
    </td>
    <td width="50%">
      <h3>💬 지능형 다국어 챗봇</h3>
      <p>의존성 그래프와 하이브리드 RAG를 결합하여 코드에 대해 질문하세요. 한국어와 영어 중 설정한 언어로 실시간 답변을 받을 수 있습니다.</p>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📄 글로벌 Auto-Docs</h3>
      <p>단순 번역이 아닌, 프로젝트 구조를 반영한 고품질 README를 멀티 랭귀지로 생성합니다. 여러 국가를 선택하여 다국어 문서를 동시 빌드할 수 있습니다.</p>
    </td>
    <td width="50%">
      <h3>🔀 Hybrid LLM 엔진</h3>
      <p>효율적인 <strong>HuggingFace (Eco)</strong>와 압도적 속도의 <strong>Groq (Llama 3.3)</strong>를 자유롭게 전환하며 사용합니다. 모든 모델은 무료 또는 오픈소스 기반으로 동작합니다.</p>
    </td>
  </tr>
</table>

---

## ⚙️ 핵심 아키텍처

### 1. AI Auto-Docs Multi-Agent Pipeline

ChatFolio의 문서화 엔진은 LangGraph로 구성된 4단계 자율 에이전트 시스템입니다.

```mermaid
graph LR
    A(📥 GitHub URL) --> B

    subgraph Pipeline ["🤖 Multi-Agent Workflow"]
        B[🔍 Analyzer\n프로젝트 정체성 식별] -->|아키타입 분류| C[🔀 Router\n최적 전략 수립]
        C --> D[✍️ Writer\n마크다운 초안 작성]
        D --> E{🕵️ Reviewer\n품질 검토}
        E -->|수정 필요| D
        E -->|승인| F
    end

    F(📄 Final README)
```

|   에이전트   | 역할                                                                                 |
| :----------: | ------------------------------------------------------------------------------------ |
| **Analyzer** | 설정 파일 및 언어 분포를 스캔하여 프로젝트 아키타입(Backend / Mobile / ML 등)을 식별 |
|  **Router**  | 식별된 아키타입에 따라 강조할 기술 스택과 섹션 구성을 결정                           |
|  **Writer**  | 의존성 그래프의 핵심 파일 스니펫을 바탕으로 마크다운 초안 작성                       |
| **Reviewer** | Getting Started 유효성, 기술적 정확도를 검토하고 Writer에 피드백 루프 실행           |

<br/>

### 2. Dynamic Identity Inference (지능형 프로젝트 식별)

URL 수집 단계부터 프로젝트의 정체성을 동적으로 파악합니다.

```
GitHub Repository
      │
      ├─ 📋 Manifest Discovery   ← package.json / build.gradle / requirements.txt 우선 탐색
      │                              → "이건 Android 프로젝트구나"
      │
      ├─ 📊 Graph Centrality     ← NetworkX In-degree 분석
      │                              → 가장 많이 참조된 파일 = 프로젝트 심장부
      │
      └─ 🔤 Language Weighting   ← 전체 파일 확장자 분포 계산
                                     → .kt 90% → Kotlin 특화 분석 가이드 전달
```

---

### 3. Data Collection Pipeline (10 Steps)

GitHub URL이 입력되는 순간부터 RAG 엔진이 준비될 때까지, 총 10단계의 파이프라인이 실행됩니다.

```
 Step 01  🔐 Auth            사용자 PAT 유효성 검증, Rate Limit 체크
    ↓
 Step 02  🔍 Cache Check     GitHub API로 최신 커밋 SHA 확인 → 캐시 재사용 or 재분석 결정
    ↓
 Step 03  📡 Scan            재귀 디렉토리 순회, .md/.txt 등 기존 문서 배제 및 코드 위주 필터링
    ↓
 Step 04  📥 Fetch           Python Generator 스트리밍으로 대용량 파일 OOM 없이 로드
    ↓
 Step 05  ✂️ Chunking        RecursiveCharacterTextSplitter를 이용한 의미 단위 코드 분할
    ↓
 Step 06  🔢 Embedding       BAAI/BGE-M3 기반 초정밀 멀티링구얼 벡터 변환
    ↓
 Step 07  🗄️ Indexing        ChromaDB 벡터 스토어 및 BM25 키워드 인덱스 동시 구축
    ↓
 Step 08  🔍 Hybrid Search   벡터 유사도와 키워드 빈도를 결합한 하이브리드 검색 수행
    ↓
 Step 09  📊 LLM Re-ranking  Llama 3.1 8B를 이용한 검색 결과 지능형 재정렬 및 필터링
    ↓
 Step 10  🤖 Agentic RAG     Qwen 3.6 MoE 에이전트가 최종 컨텍스트를 분석하여 답변 생성
```

<br/>

### 4. Multi-Language Parser Support

`Factory Pattern` 기반의 파서 라우터가 파일 확장자를 감지하여 최적의 분석기를 자동으로 배정합니다.

#### 🔤 Language Parsers (`core/parser/lang/`)

|            언어             |        파서        | 주요 추출 항목                            |
| :-------------------------: | :----------------: | ----------------------------------------- |
|         **Python**          |   `ts_python.py`   | `class`, `def`, `import`, `from`          |
| **JavaScript / TypeScript** | `ts_javascript.py` | `function`, `const`, `import`, `export`   |
|          **Java**           |    `ts_java.py`    | `class`, `interface`, `method`, `package` |
|         **Kotlin**          |   `ts_kotlin.py`   | `class`, `fun`, `object`, `import`        |
|           **Go**            |     `ts_go.py`     | `func`, `struct`, `package`, `import`     |
|           **C++**           |    `ts_cpp.py`     | `class`, `function`, `#include`           |
|           **C#**            |   `ts_csharp.py`   | `class`, `namespace`, `using`             |
|          **Rust**           |    `ts_rust.py`    | `fn`, `struct`, `mod`, `use`              |
|          **Swift**          |   `ts_swift.py`    | `class`, `struct`, `func`, `import`       |
|          **Dart**           |    `ts_dart.py`    | `class`, `void`, `import`                 |
|           **PHP**           |    `ts_php.py`     | `class`, `function`, `namespace`, `use`   |
|          **Ruby**           |    `ts_ruby.py`    | `class`, `def`, `module`, `require`       |

#### ⚙️ Config Parsers (`core/parser/config/`)

|    형식    |        파서        | 용도                                     |
| :--------: | :----------------: | ---------------------------------------- |
| **Gradle** | `gradle_parser.py` | Android / Spring 의존성, 빌드 설정 추출  |
|  **JSON**  |  `json_parser.py`  | `package.json` 등 패키지 메타데이터 파싱 |
|  **YAML**  |  `yaml_parser.py`  | Docker Compose, CI/CD 설정 추출          |
|  **XML**   |  `xml_parser.py`   | `pom.xml`, `AndroidManifest.xml` 파싱    |
|  **SQL**   |  `sql_parser.py`   | DB 스키마 및 테이블 구조 추출            |

> 지원되지 않는 확장자는 기본 메타데이터 추출기(Fallback)로 처리되어 분석이 중단되지 않습니다.

---

## 🛠 기술 스택

<table>
  <tr>
    <th>영역</th>
    <th>기술</th>
  </tr>
  <tr>
    <td><strong>Frontend</strong></td>
    <td>
      React 18 (Vite) · Vanilla CSS · Zustand<br/>
      react-force-graph-2d · react-markdown · Lucide React
    </td>
  </tr>
  <tr>
    <td><strong>Backend</strong></td>
    <td>
      FastAPI (Python 3.10+) · LangGraph · LangChain<br/>
      Groq Llama 3.3 · HuggingFace Mistral · NetworkX
    </td>
  </tr>
  <tr>
    <td><strong>Database</strong></td>
    <td>PostgreSQL · SQLAlchemy ORM</td>
  </tr>
  <tr>
    <td><strong>Infra</strong></td>
    <td>Docker · Docker Compose</td>
  </tr>
</table>

---

## 🚀 시작하기 (Getting Started)

### Prerequisites

- Docker & Docker Compose
- Groq API Key _(무료 티어 제공)_
- HuggingFace API Token _(선택 사항)_

### Installation

```bash
# 1. 저장소 클론
git clone https://github.com/EJ-pro/ChatFolio.git
cd ChatFolio

# 2. 환경 변수 설정
cp .env.sample .env
# .env 파일을 열어 API Key를 입력합니다

# 3. 실행
docker-compose up --build
```

> ✅ 실행 후 브라우저에서 `http://localhost` 로 접속하세요.

---

## 📂 폴더 구조

```
ChatFolio/
├── backend/
│   ├── core/
│   │   ├── rag/            # ChatFolioEngine, ReadmeAgent (Multi-Agent)
│   │   ├── parser/         # GitHub Fetcher, AST 파서 (다국어 지원)
│   │   └── graph/          # NetworkX 기반 의존성 그래프 빌더
│   ├── database/           # PostgreSQL 세션 및 ORM 모델
│   ├── models/             # Pydantic 스키마
│   └── main.py             # FastAPI 엔드포인트
├── frontend/
│   └── src/
│       ├── pages/          # Analysis, Chat, DocsTab, DocPipeline
│       ├── components/     # 레이아웃, 공통 UI
│       └── store/          # Zustand 전역 상태
├── .env.sample
└── docker-compose.yml
```

---

<div align="center">

**EJ-pro** · [GitHub](https://github.com/EJ-pro/ChatFolio)

_ChatFolio — 코드를 읽는 시간을, 만드는 시간으로._

</div>
