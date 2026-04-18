# 🚀 ChatFolio
> "AI 기반 지능형 레포지토리 분석 및 자동 문서화 플랫폼" <br/>
> 복잡한 코드베이스의 의존성을 한눈에 파악하고, AI와 대화하며, 클릭 한 번으로 고품질 README를 생성하세요.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![React](https://img.shields.io/badge/React-18.x-61DAFB.svg?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95-009688.svg?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-Python-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

<br/>

## 📝 목차
1. [프로젝트 소개](#-프로젝트-소개)
2. [주요 기능](#-주요-기능-key-features)
3. [기술 스택](#-기술-스택-tech-stack)
4. [화면 구성 및 사용법](#-화면-구성-및-사용법-usage)
5. [시작하기](#-시작하기-getting-started)
6. [폴더 구조](#-폴더-구조-directory-structure)

<br/>

## 💡 프로젝트 소개
새로운 오픈소스 프로젝트에 참여하거나 거대한 레거시 코드를 인수인계받을 때, 코드를 파악하는 것은 엄청난 시간이 소모되는 작업입니다. 
**ChatFolio**는 GitHub 레포지토리를 연동하기만 하면 코드 간의 의존성 그래프(Dependency Graph)를 추출하고, 이를 기반으로 AI와 문답(RAG)하거나 고품질의 문서를 자동으로 작성해 주는 혁신적인 개발자 생산성 도구입니다.

<br/>

## ✨ 주요 기능 (Key Features)
- 🕸 **의존성 시각화 (Architecture Graph):** `NetworkX`로 분석된 코드 의존성을 물리 엔진 기반의 `react-force-graph`로 동적 렌더링하여 아키텍처를 한눈에 파악.
- 💬 **AI 코드 챗봇 (RAG):** `LangChain`과 `OpenAI`를 활용하여 레포지토리의 구조와 비즈니스 로직에 대해 실시간으로 질문하고 답변 획득.
- 📄 **원클릭 자동 문서화 (Auto-Docs):** 단순히 파일명만 읽는 것이 아니라, 가장 많이 참조된 핵심 파일(Degree Centrality 활용)의 코드를 읽어 비즈니스 로직을 추론한 고품질 `README.md` 자동 생성. 5가지 커스텀 템플릿 지원.
- 🐳 **도커 기반 풀스택 컨테이너화:** FastAPI, React, PostgreSQL 환경을 `docker-compose` 하나로 완벽하게 구축.

<br/>

## 🛠 기술 스택 (Tech Stack)

### Frontend
- **Framework:** React 18 (Vite)
- **Styling:** TailwindCSS, Lucide-React
- **State Management:** Zustand
- **Visualization:** `react-force-graph-2d`, `react-markdown`

### Backend
- **Framework:** FastAPI (Python 3.10+)
- **AI/LLM:** LangChain, OpenAI GPT-4, NetworkX (Graph Analysis)
- **Database:** PostgreSQL, SQLAlchemy (ORM)

### Infra & Tools
- **Deployment:** Docker, Docker Compose
- **Version Control:** Git

<br/>

## 📱 화면 구성 및 사용법 (Usage)
> 💡 ChatFolio의 주요 탭 기능 소개입니다.

| 아키텍처 시각화 (Architecture) | 자동 문서화 (DocsTab) |
| :---: | :---: |
| <img src="https://via.placeholder.com/400x250.png?text=Graph+Visualization" width="400"/> | <img src="https://via.placeholder.com/400x250.png?text=Auto+Readme+Generator" width="400"/> |
| 노드 크기와 엣지 연결을 통해 가장 중요한 핵심 파일(Core Files)을 시각적으로 탐색합니다. | 템플릿을 선택하고 버튼을 누르면 AI가 레포지토리를 분석해 README 마크다운을 렌더링합니다. |

<br/>

## 🚀 시작하기 (Getting Started)

### 1. 요구 사항 (Prerequisites)
- Docker & Docker Compose
- OpenAI API Key (LLM 분석용)

### 2. 설치 및 실행 (Installation)
```bash
# 1. 저장소 클론
$ git clone https://github.com/EJ-pro/ChatFolio.git
$ cd ChatFolio

# 2. 환경 변수 설정
# .env.sample 파일을 참고하여 .env 파일을 생성하고 OpenAI API Key를 입력하세요.
$ cp .env.sample .env

# 3. 도커 컴포즈 실행
$ docker-compose up --build
```
> 서버가 실행되면 브라우저에서 `http://localhost` 로 접속하여 서비스를 이용할 수 있습니다!

<br/>

## 📂 폴더 구조 (Directory Structure)
```text
ChatFolio/
 ├── backend/
 ┃    ├── core/           # RAG 엔진, Github 파서, 그래프 분석기
 ┃    ├── database/       # PostgreSQL 연결 세션 및 세팅
 ┃    ├── models/         # Pydantic 스키마 및 DB 엔티티
 ┃    └── main.py         # FastAPI 엔드포인트
 ├── frontend/
 ┃    ├── src/
 ┃    ┃    ├── pages/       # 분석 대시보드, RAG 채팅, 문서화 탭
 ┃    ┃    ├── components/  # 레이아웃, 공통 UI 컴포넌트
 ┃    ┃    └── store/       # Zustand 상태 관리 (Zustand)
 ┃    └── package.json
 ├── .env.sample          # 환경 변수 예시
 └── docker-compose.yml   # 컨테이너 오케스트레이션
```

<br/>

## 👨‍💻 기여 (Contact)
- **EJ-pro** - [GitHub Repository](https://github.com/EJ-pro/ChatFolio)