import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ShieldCheck, Github } from 'lucide-react';
import UserProfile from '../components/UserProfile';

function Privacy() {
  const navigate = useNavigate();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative font-sans overflow-x-hidden">
      {/* Background Orbs - Fixed to prevent scrolling issues */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[50%] h-[50%] bg-blue-600/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[50%] h-[50%] bg-purple-600/10 blur-[120px] rounded-full"></div>
      </div>

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

      <main className="flex-grow w-full max-w-4xl mx-auto p-6 md:p-10 relative z-10 pb-20">
        <div className="glass-panel rounded-3xl p-8 md:p-12 border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-blue-500 to-purple-600"></div>
          
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-400 border border-blue-500/20">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h1 className="text-4xl font-black text-white tracking-tight">개인정보 처리방침</h1>
          </div>

          <div className="space-y-8 text-slate-400 leading-relaxed">
            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                제1조 (수집하는 개인정보 항목)
              </h2>
              <p>서비스는 원활한 서비스 제공을 위해 다음과 같은 정보를 수집합니다.</p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li><span className="text-slate-200">GitHub 연동 시:</span> GitHub ID, 이메일, 이름, 아바타 URL, GitHub 액세스 토큰.</li>
                <li><span className="text-slate-200">서비스 이용 과정:</span> 분석 요청한 레포지토리 URL, 코드 내용(분석용), AI와의 채팅 내역.</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                제2조 (개인정보의 이용 목적)
              </h2>
              <p>수집된 정보는 다음의 목적을 위해 활용됩니다.</p>
              <ul className="list-disc pl-6 mt-2 space-y-1">
                <li>서비스 제공 및 이용자 본인 확인</li>
                <li>맞춤형 코드 의존성 분석 및 기술 스택 파악</li>
                <li>개발자 페르소나(MBTI) 정의 및 시각화 데이터 생성</li>
                <li>서비스 개선을 위한 통계적 분석</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                제3조 (GitHub 액세스 토큰 관리)
              </h2>
              <p>
                이용자의 <span className="text-blue-400 font-mono">GitHub 액세스 토큰</span>은 프라이빗 레포지토리의 코드를 읽어오기 위한 용도로만 사용되며, 서버 내에 암호화되어 안전하게 저장됩니다. 이용자가 서비스 연동을 해제하거나 계정을 삭제할 경우, 해당 토큰 및 관련 정보는 즉시 복구 불가능한 방법으로 파기됩니다.
              </p>
            </section>

            <section>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                제4조 (정보의 제3자 제공)
              </h2>
              <p>
                ChatFolio는 이용자의 사전 동의 없이 개인정보를 외부에 제공하지 않습니다. 다만, AI 분석을 위해 이용되는 코드 데이터는 API 제공사(OpenAI, Groq 등)를 통해 처리될 수 있으며, 이 과정에서 개인 식별 정보는 제외됩니다.
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

export default Privacy;
