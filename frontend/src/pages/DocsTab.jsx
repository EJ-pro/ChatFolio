import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { FileText, Loader2, Copy, Sparkles, CheckCircle2, Eye, Code } from 'lucide-react';
import ReactMarkdown from 'react-markdown';


const DEFAULT_EXAMPLE = `# 🚀 AwesomeProject\n> "개발자를 위한 최고의 생산성 도구" <br/>\n> 업무 효율을 200% 끌어올려주는 실시간 협업 플랫폼입니다.\n\n![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)\n![React](https://img.shields.io/badge/React-18.0-61DAFB.svg?logo=react)\n![FastAPI](https://img.shields.io/badge/FastAPI-0.95-009688.svg?logo=fastapi)\n![License](https://img.shields.io/badge/license-MIT-green.svg)\n\n<br/>\n\n## 📝 목차\n1. [프로젝트 소개](#-프로젝트-소개)\n2. [주요 기능](#-주요-기능-key-features)\n3. [기술 스택](#-기술-스택-tech-stack)\n4. [화면 구성 및 사용법](#-화면-구성-및-사용법-usage)\n5. [시작하기](#-시작하기-getting-started)\n6. [폴더 구조](#-폴더-구조-directory-structure)\n\n<br/>\n\n## 💡 프로젝트 소개\n기존의 협업 툴들이 가진 [어떤 문제점/불편함]을 해결하기 위해 기획되었습니다. \n단순한 텍스트 공유를 넘어, 실시간 동기화와 직관적인 UX를 통해 팀의 커뮤니케이션 비용을 최소화하는 것이 목표입니다.\n\n<br/>\n\n## ✨ 주요 기능 (Key Features)\n- ⚡ **0.1초 실시간 동기화:** WebSocket(Socket.io)을 활용한 지연 없는 데이터 통신 및 상태 공유\n- 🎨 **완벽한 다크모드 지원:** TailwindCSS 기반의 테마 시스템으로 사용자의 눈 피로도 최소화\n- 🔒 **안전한 인증 시스템:** JWT 기반의 토큰 발급 및 OAuth 2.0 (Google, Github) 소셜 로그인 지원\n- 📊 **대시보드 통계:** 사용자 활동 데이터를 차트(Chart.js)로 시각화하여 제공\n\n<br/>\n\n## 🛠 기술 스택 (Tech Stack)\n### Frontend\n- **Framework:** React 18\n- **Styling:** TailwindCSS, Framer Motion (애니메이션)\n- **State Management:** Zustand / React Query\n\n### Backend\n- **Framework:** FastAPI (Python 3.10+)\n- **Database:** PostgreSQL, SQLAlchemy (ORM)\n- **Real-time:** WebSockets\n\n### Infra & Tools\n- **Deployment:** Docker, AWS EC2, Vercel\n- **Version Control:** Git, Github Actions (CI/CD)\n\n<br/>\n\n## 📱 화면 구성 및 사용법 (Usage)\n> 💡 실제 구현된 화면 캡처나 GIF(움짤)를 추가하면 신뢰도가 대폭 상승합니다.\n\n| 메인 대시보드 | 실시간 채팅 화면 |\n| :---: | :---: |\n| <img src="https://via.placeholder.com/400x250.png?text=Dashboard+Screenshot" width="400"/> | <img src="https://via.placeholder.com/400x250.png?text=Chat+Screenshot" width="400"/> |\n| 대시보드에서 프로젝트 전체 진행률을 확인합니다. | 웹소켓을 통한 실시간 채팅 및 파일 공유 화면입니다. |\n\n<br/>\n\n## 🚀 시작하기 (Getting Started)\n프로젝트를 로컬에서 직접 실행해보기 위한 가이드입니다.\n\n### 1. 요구 사항 (Prerequisites)\n- Node.js 18.0 이상\n- Python 3.10 이상\n- PostgreSQL 14 이상\n\n### 2. 설치 및 실행 (Installation)\n\`\`\`bash\n# 1. 저장소 클론\n$ git clone [https://github.com/username/AwesomeProject.git](https://github.com/username/AwesomeProject.git)\n\n# 2. 프론트엔드 종속성 설치 및 실행\n$ cd frontend\n$ npm install\n$ npm run dev\n\n# 3. 백엔드 환경 설정 및 실행 (새 터미널)\n$ cd backend\n$ pip install -r requirements.txt\n$ uvicorn main:app --reload\n\`\`\`\n\n<br/>\n\n## 📂 폴더 구조 (Directory Structure)\n\`\`\`text\n📦 AwesomeProject\n ┣ 📂 frontend\n ┃ ┣ 📂 src\n ┃ ┃ ┣ 📂 components   # 공통으로 사용되는 UI 컴포넌트\n ┃ ┃ ┣ 📂 pages        # 라우팅되는 페이지 단위 컴포넌트\n ┃ ┃ ┣ 📂 hooks        # 커스텀 훅 모음\n ┃ ┃ ┗ 📂 utils        # 유틸리티 함수 (날짜 변환, 포맷팅 등)\n ┃ ┗ 📜 package.json\n ┣ 📂 backend\n ┃ ┣ 📂 api            # 라우터 및 엔드포인트 정의\n ┃ ┣ 📂 core           # 인증, 설정 등 핵심 로직\n ┃ ┣ 📂 models         # DB 모델 (SQLAlchemy)\n ┃ ┗ 📜 main.py\n ┗ 📜 README.md\n\`\`\`\n\n<br/>\n\n## 👨‍💻 팀원 및 기여 (Contact)\n홍길동 - Frontend & UI/UX - Github 링크\n김개발 - Backend & Infra - Github 링크\n`;

function DocsTab() {
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  
  const [readmeContent, setReadmeContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [hasLoadedExisting, setHasLoadedExisting] = useState(false);
  const [viewMode, setViewMode] = useState('code'); // 'code' or 'md'

  // 컴포넌트 마운트 시 기존에 생성된 README가 있는지 확인
  useEffect(() => {
    if (sessionId && !hasLoadedExisting) {
      fetchExistingReadme();
    }
  }, [sessionId]);

  const fetchExistingReadme = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/generate/readme', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          session_id: sessionId,
          force_regenerate: false // 기존 거 있으면 가져오기
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.readme_content) {
          setReadmeContent(data.readme_content);
        }
      }
    } catch (err) {
      console.error('Failed to fetch existing readme:', err);
    } finally {
      setHasLoadedExisting(true);
    }
  };

  const handleGenerateReadme = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    setError('');
    setReadmeContent('');
    setCopied(false);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/generate/readme', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          session_id: sessionId,
          force_regenerate: true
        })
      });

      if (!response.ok) {
        throw new Error('README 생성 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setReadmeContent(data.readme_content);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(readmeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex h-full bg-slate-950 overflow-hidden">
      {/* Left Panel: Controls */}
      <div className="w-1/3 min-w-[350px] p-8 bg-slate-900/30 border-r border-white/5 overflow-y-auto">
        <header className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-bold mb-4 border border-blue-500/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Auto-Docs</span>
          </div>
          <h2 className="text-3xl font-black text-white mb-2 tracking-tight">문서 자동화</h2>
          <p className="text-slate-400 text-sm leading-relaxed">프로젝트 아키텍처와 핵심 코드를 분석하여 고품질의 문서를 생성합니다.</p>
        </header>

        <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 shadow-2xl backdrop-blur-xl relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-600"></div>
          <div className="w-12 h-12 bg-blue-500/10 text-blue-400 rounded-2xl flex items-center justify-center mb-4 border border-blue-500/20">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white mb-2">README 생성기</h3>
          <p className="text-slate-400 text-sm mb-6 leading-relaxed">
            전체 파일 개수, 가장 많이 참조된 핵심 파일 Top 5, 그리고 디렉토리 구조를 바탕으로 Github에 올릴 수 있는 README.md를 자동 작성합니다.
          </p>
          
          <button
            onClick={handleGenerateReadme}
            disabled={isLoading || !sessionId}
            className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-bold shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>README 생성 중...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>README 자동 생성 🚀</span>
              </>
            )}
          </button>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg text-center font-medium">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel: Viewer */}
      <div className="flex-1 bg-slate-950 overflow-hidden flex flex-col relative">
        {/* Background Gradients */}
        <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/5 blur-[100px] rounded-full pointer-events-none"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/5 blur-[100px] rounded-full pointer-events-none"></div>

        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8 z-10 text-slate-500">
            <div className="relative mb-6">
              <Loader2 className="w-16 h-16 text-blue-500 animate-spin" />
              <Sparkles className="absolute -top-2 -right-2 w-6 h-6 text-yellow-400 animate-pulse" />
            </div>
            <p className="text-white font-bold text-xl mb-2">AI가 아키텍처를 심층 분석 중입니다...</p>
            <p className="text-slate-400 text-sm">이 작업은 약 10~20초 정도 소요됩니다. 잠시만 기다려 주세요.</p>
          </div>
        ) : readmeContent ? (
          <>
            <div className="flex-1 overflow-y-auto p-10 custom-scrollbar z-10">
              <div className="max-w-4xl mx-auto bg-slate-900/80 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden min-h-full border border-white/10">
                <div className="bg-white/5 border-b border-white/10 px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-blue-400" />
                    <span className="text-sm font-bold text-white tracking-tight">README.md (Generated)</span>
                  </div>
                  <div className="flex items-center gap-4">
                    {/* View Toggle */}
                    <div className="flex items-center bg-slate-900/50 rounded-lg p-1 border border-white/10">
                      <button
                        onClick={() => setViewMode('code')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                          viewMode === 'code' ? 'bg-blue-600/20 text-blue-400 shadow-sm' : 'text-slate-500 hover:text-slate-300'
                        }`}
                      >
                        <Code className="w-3.5 h-3.5" />
                        Code
                      </button>
                      <button
                        onClick={() => setViewMode('md')}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                          viewMode === 'md' ? 'bg-indigo-600/20 text-indigo-400 shadow-sm' : 'text-slate-500 hover:text-slate-300'
                        }`}
                      >
                        <Eye className="w-3.5 h-3.5" />
                        MD
                      </button>
                    </div>

                    <button
                      onClick={copyToClipboard}
                      className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-xl border border-white/10 transition-all text-xs font-bold"
                    >
                      {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                      {copied ? '복사됨' : '복사'}
                    </button>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">AI Optimized</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-10">
                  {viewMode === 'md' ? (
                    <div className="prose prose-invert max-w-none prose-headings:text-white prose-headings:font-black prose-a:text-blue-400 prose-pre:bg-black/50 prose-pre:border prose-pre:border-white/10 prose-pre:rounded-2xl">
                      <ReactMarkdown>{readmeContent}</ReactMarkdown>
                    </div>
                  ) : (
                    <pre className="p-6 bg-slate-950/80 rounded-2xl border border-white/10 text-slate-300 text-sm font-mono overflow-x-auto custom-scrollbar shadow-inner leading-relaxed whitespace-pre-wrap break-all">
                      <code>{readmeContent}</code>
                    </pre>
                  )}
                </div>
              </div>
            </div>

          </>
        ) : (
          <div className="flex-1 overflow-y-auto p-10 custom-scrollbar relative z-10">
            <div className="max-w-4xl mx-auto bg-slate-900/40 backdrop-blur-md rounded-3xl shadow-2xl overflow-hidden min-h-full border border-white/5 relative opacity-60 hover:opacity-100 transition-all duration-500 group/preview">
              <div className="bg-white/5 border-b border-white/10 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Eye className="w-5 h-5 text-slate-400" />
                  <span className="text-sm font-bold text-slate-300 tracking-tight">스타일 미리보기 (Preview)</span>
                </div>
                <span className="text-[10px] font-bold text-slate-500 bg-white/5 px-2 py-1 rounded-lg border border-white/5 uppercase tracking-widest">
                  Standard Professional
                </span>
              </div>
              
              <div className="p-10 prose prose-invert prose-slate max-w-none opacity-50 grayscale group-hover/preview:grayscale-0 group-hover/preview:opacity-100 transition-all duration-700">
                <ReactMarkdown>{DEFAULT_EXAMPLE}</ReactMarkdown>
              </div>
              
              {/* Preview Watermark */}
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center overflow-hidden">
                <span className="transform -rotate-12 text-8xl font-black text-white/[0.03] uppercase tracking-[2em] select-none">
                  Preview
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DocsTab;
