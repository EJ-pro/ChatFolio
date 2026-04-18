import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      localStorage.setItem('token', token);
      navigate('/');
    } else {
      alert("인증에 실패했습니다. 다시 시도해주세요.");
      navigate('/login');
    }
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
      <h2 className="text-xl font-bold text-slate-800">로그인 중입니다...</h2>
      <p className="text-slate-500 mt-2">잠시만 기다려주세요.</p>
    </div>
  );
}

export default AuthCallback;
