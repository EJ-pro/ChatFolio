import { useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, Github } from 'lucide-react';
import UserProfile from '../components/UserProfile';

function Terms() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative overflow-x-hidden font-sans">
      <div className="absolute top-[-10%] right-[-5%] w-[50%] h-[50%] bg-blue-600/10 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[-10%] left-[-5%] w-[50%] h-[50%] bg-purple-600/10 blur-[120px] rounded-full pointer-events-none"></div>

      <header className="w-full px-8 py-4 flex justify-between items-center sticky top-0 z-50 backdrop-blur-md border-b border-white/5 bg-slate-950/50">
        <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors group">
          <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
          <span className="font-bold">Back</span>
        </button>
        <div className="flex items-center gap-2" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <Github className="w-6 h-6 text-white" />
          <span className="font-black tracking-tighter text-xl">ChatFolio</span>
        </div>
        <UserProfile />
      </header>

      <main className="flex-1 w-full max-w-4xl mx-auto p-6 md:p-10 relative z-10">
        <div className="glass-panel rounded-3xl p-8 md:p-12 border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 to-purple-600"></div>
          
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-400 border border-purple-500/20">
              <FileText className="w-6 h-6" />
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">서비스 이용약관</h1>
          </div>

          <div className="space-y-8 text-slate-400 leading-relaxed">
            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full"></span>
                제1조 (목적)
              </h2>
              <p>
                본 약관은 ChatFolio(이하 "서비스")가 제공하는 모든 서비스의 이용 조건 및 절차, 이용자와 서비스 운영자의 권리, 의무 및 책임 사항을 규정함을 목적으로 합니다.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full"></span>
                제2조 (서비스의 내용)
              </h2>
              <p>ChatFolio는 이용자에게 다음과 같은 기능을 제공합니다.</p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>GitHub 레포지토리 의존성 분석 및 시각화</li>
                <li>AI 기반의 코드 설명 및 질의응답</li>
                <li>자동화된 프로젝트 README 및 포트폴리오 문서 생성</li>
                <li>개발자 기술 스택 및 페르소나 분석</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full"></span>
                제3조 (이용자의 의무)
              </h2>
              <ul className="list-disc pl-6 space-y-1">
                <li>이용자는 본인의 GitHub 계정 및 액세스 토큰을 안전하게 관리해야 합니다.</li>
                <li>타인의 지적재산권을 침해하거나 서비스 운영에 지장을 주는 행위를 금지합니다.</li>
                <li>분석된 결과물을 상업적으로 이용할 경우, 원본 코드의 라이선스 규정을 준수해야 합니다.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full"></span>
                제4조 (서비스의 중단 및 변경)
              </h2>
              <p>
                서비스는 운영상 또는 기술상의 필요에 따라 제공하는 서비스의 전부 또는 일부를 변경하거나 중단할 수 있습니다. 이 경우 사이트 공지사항이나 이메일을 통해 사전에 통지합니다.
              </p>
            </section>
          </div>

          <div className="mt-12 pt-8 border-t border-white/5 text-sm text-slate-500">
            시행 일자: 2026년 4월 20일
          </div>
        </div>
      </main>

      <footer className="w-full text-center p-10 text-slate-600 text-sm border-t border-white/5 mt-20">
        &copy; 2026 ChatFolio. Designed for the Next Generation of Developers.
      </footer>
    </div>
  );
}

export default Terms;
