import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { MessageSquare, FileText, Target, Github, LogOut } from 'lucide-react';
import { useEffect } from 'react';

function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const sessionId = location.state?.sessionId;

  // 세션이 없으면 홈으로 (Analysis)
  useEffect(() => {
    if (!sessionId) {
      alert("유효한 세션이 없습니다. 분석을 먼저 진행해주세요.");
      navigate('/');
    }
  }, [sessionId, navigate]);

  const navItems = [
    { path: '/dashboard/chat', icon: MessageSquare, label: '일반 채팅' },
    { path: '/dashboard/docs', icon: FileText, label: '문서 자동화' },
    { path: '/dashboard/interview', icon: Target, label: '모의 면접' },
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shadow-xl z-10">
        <div className="p-6 flex items-center gap-3 border-b border-slate-800">
          <Github className="w-8 h-8 text-white" />
          <h1 className="text-xl font-bold text-white tracking-wide">ChatFolio</h1>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              state={{ sessionId }} // 세션 ID 유지
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800 space-y-2">
          <button
            onClick={() => navigate('/')}
            className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            <Target className="w-5 h-5" />
            <span className="font-medium">새로운 분석하기</span>
          </button>
          
          <button
            onClick={() => {
              localStorage.removeItem('token');
              navigate('/login');
            }}
            className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">로그아웃</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-white relative">
        <Outlet />
      </main>
    </div>
  );
}

export default DashboardLayout;
