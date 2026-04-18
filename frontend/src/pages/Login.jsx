import { Github, Chrome } from 'lucide-react';
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

  const handleGoogleLogin = () => {
    window.location.href = 'http://localhost:8000/auth/google/login';
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-100 p-10 text-center">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-slate-900 rounded-2xl flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-0 transition-all duration-300">
            <Github className="w-10 h-10 text-white" />
          </div>
        </div>
        
        <h1 className="text-3xl font-extrabold text-slate-900 mb-2">ChatFolio</h1>
        <p className="text-slate-500 mb-10">당신의 레포지토리를 가장 완벽하게 분석하는 방법</p>

        <button
          onClick={handleGithubLogin}
          className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-slate-900 text-white rounded-xl font-semibold text-lg hover:bg-slate-800 transition-all shadow-md hover:shadow-xl transform hover:-translate-y-1 mb-4"
        >
          <Github className="w-6 h-6" />
          <span>Continue with GitHub</span>
        </button>

        <button
          onClick={handleGoogleLogin}
          className="w-full flex items-center justify-center gap-3 py-4 px-6 bg-white text-slate-700 rounded-xl font-semibold text-lg hover:bg-slate-50 transition-all shadow-sm border border-slate-200 transform hover:-translate-y-1"
        >
          <Chrome className="w-6 h-6 text-blue-500" />
          <span>Continue with Google</span>
        </button>
      </div>
    </div>
  );
}

export default Login;
