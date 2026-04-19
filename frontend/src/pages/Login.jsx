import { Github } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

function Login() {
  const navigate = useNavigate();

  useEffect(() => {
    // 로컬스토리지에 토큰이 있으면 바로 메인으로
    if (localStorage.getItem('token')) {
      navigate('/');
    }
  }, [navigate]);

  const handleGithubLogin = () => {
    window.location.href = 'http://localhost:8000/auth/github/login';
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-4 relative overflow-hidden font-sans">
      {/* Background Decorative Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 blur-[120px] rounded-full pointer-events-none"></div>

      <div className="w-full max-w-md bg-slate-800/50 backdrop-blur-md rounded-3xl shadow-2xl overflow-hidden border border-slate-700/50 p-10 text-center relative z-10">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-slate-950 rounded-2xl flex items-center justify-center shadow-lg border border-slate-800 transform rotate-3 hover:rotate-0 transition-all duration-300">
            <Github className="w-10 h-10 text-white" />
          </div>
        </div>

        <h1 className="text-3xl font-extrabold text-white mb-2">ChatFolio</h1>
        <p className="text-slate-400 mb-10">당신의 레포지토리를 가장 완벽하게 분석하는 방법</p>

        <button
          onClick={handleGithubLogin}
          className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-slate-950 text-white rounded-xl font-semibold text-lg border border-slate-700 hover:bg-black transition-all shadow-md hover:shadow-xl transform hover:-translate-y-1 mb-8"
        >
          <Github className="w-6 h-6" />
          <span>Continue with GitHub</span>
        </button>

        <div className="flex justify-center gap-4 text-xs text-slate-500 font-medium mb-6">
          <button onClick={() => navigate('/terms')} className="hover:text-white transition-colors">이용약관</button>
          <span className="opacity-20">|</span>
          <button onClick={() => navigate('/privacy')} className="hover:text-white transition-colors">개인정보 처리방침</button>
          <span className="opacity-20">|</span>
          <button onClick={() => navigate('/faq')} className="hover:text-white transition-colors">고객센터(FAQ)</button>
        </div>

        <div className="pt-6 border-t border-white/5 text-[10px] text-slate-600 space-y-1">
          <p>대표 : 이재희 | TEL : 02-529-4237</p>
          <p>Mail : ChatFolio@chatfolio.com</p>
          <p className="pt-2">&copy; 2026 ChatFolio. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}

export default Login;
