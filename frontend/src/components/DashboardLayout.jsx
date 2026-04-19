import { Outlet, NavLink, useLocation, useNavigate, useParams } from 'react-router-dom';
import { MessageSquare, FileText, Target, Github, LogOut, Share2, Search, Bell, GitBranch, ChevronDown } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import UserProfile from './UserProfile';



function DashboardLayout() {
  const { username } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  // URL state에서 가져오거나 sessionStorage에서 복구
  const sessionId = location.state?.sessionId || sessionStorage.getItem('last_session_id');

  const [projects, setProjects] = useState([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  
  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        const res = await fetch('http://localhost:8000/projects', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setProjects(data);
        }
      } catch (err) {
        console.error("Failed to fetch projects:", err);
      }
    };
    fetchProjects();
  }, []);

  useEffect(() => {
    if (location.state?.sessionId) {
      sessionStorage.setItem('last_session_id', location.state.sessionId);
    }
  }, [location.state?.sessionId]);

  // 세션이 없으면 홈으로 (Analysis)
  useEffect(() => {
    if (!sessionId) {
      alert("유효한 세션이 없습니다. 분석을 먼저 진행해주세요.");
      navigate(`/${username}/analysis`);
    }
  }, [sessionId, navigate, username]);

  const navItems = [
    { path: `/${username}/dashboard/chat`, icon: MessageSquare, label: '일반 채팅' },
    { path: `/${username}/dashboard/architecture`, icon: Share2, label: '아키텍처' },
    { path: `/${username}/dashboard/docs`, icon: FileText, label: '문서 자동화' },
    { path: `/${username}/dashboard/interview`, icon: Target, label: '모의 면접' },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900/50 backdrop-blur-xl text-slate-300 flex flex-col border-r border-white/5 z-30">
        <div className="p-6 flex items-center gap-3 border-b border-white/5">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Github className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-xl font-black text-white tracking-tighter">ChatFolio</h1>
        </div>

        <nav className="flex-1 px-4 py-8 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              state={{ sessionId }} // 세션 ID 유지
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                    : 'hover:bg-white/5 text-slate-400 hover:text-white'
                }`
              }
            >
              <item.icon className={`w-5 h-5 transition-transform duration-300 ${location.pathname === item.path ? '' : 'group-hover:scale-110'}`} />
              <span className="font-bold text-sm tracking-tight">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5 space-y-2">
          <button
            onClick={() => navigate(`/${username}/analysis`)}
            className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:text-white hover:bg-white/5 rounded-2xl transition-all group"
          >
            <div className="p-2 rounded-lg bg-slate-800 group-hover:bg-blue-500/20 transition-colors">
              <Target className="w-4 h-4" />
            </div>
            <span className="font-bold text-sm">분석 홈으로</span>
          </button>
          
          <button
            onClick={() => {
              localStorage.removeItem('token');
              navigate('/login');
            }}
            className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-2xl transition-all group"
          >
             <div className="p-2 rounded-lg bg-red-500/10 group-hover:bg-red-500/20 transition-colors">
              <LogOut className="w-4 h-4" />
            </div>
            <span className="font-bold text-sm">로그아웃</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden bg-slate-950 relative">
        {/* Background Gradients */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-600/5 blur-[120px] rounded-full pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-600/5 blur-[120px] rounded-full pointer-events-none"></div>

        {/* Header Bar */}
        <header className="h-16 bg-slate-950/50 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-8 shrink-0 z-20">
          <div className="flex items-center gap-4">
            <div className="relative" ref={dropdownRef}>
              <button 
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-xl border border-white/5 hover:border-blue-500/30 hover:bg-white/10 transition-all min-w-[280px] group"
              >
                <GitBranch className={`w-4 h-4 ${isDropdownOpen ? 'text-blue-400' : 'text-slate-500'} group-hover:text-blue-400 transition-colors`} />
                <span className="flex-1 text-left text-sm text-slate-200 font-medium truncate">
                  {projects.find(p => p.latest_session_id === sessionId)?.repo_url.replace('https://github.com/', '') || '프로젝트 선택...'}
                </span>
                <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform duration-300 ${isDropdownOpen ? 'rotate-180 text-blue-400' : ''}`} />
              </button>

              {/* Custom Dropdown Menu */}
              {isDropdownOpen && (
                <div className="absolute top-full left-0 mt-2 w-full bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="p-2 max-h-64 overflow-y-auto custom-scrollbar">
                    {projects.filter(p => p.latest_session_id).map(p => {
                      const isActive = p.latest_session_id === sessionId;
                      return (
                        <button
                          key={p.id}
                          onClick={() => {
                            navigate(location.pathname, { state: { sessionId: p.latest_session_id }, replace: true });
                            setIsDropdownOpen(false);
                          }}
                          className={`w-full text-left px-4 py-3 rounded-xl flex flex-col gap-0.5 transition-all mb-1 last:mb-0 ${
                            isActive 
                              ? 'bg-blue-600 text-white' 
                              : 'hover:bg-white/5 text-slate-400 hover:text-white'
                          }`}
                        >
                          <span className="text-sm font-bold truncate">
                            {p.repo_url.split('/').pop()}
                          </span>
                          <span className={`text-[10px] truncate opacity-60 ${isActive ? 'text-blue-100' : 'text-slate-500'}`}>
                            {p.repo_url.replace('https://github.com/', '')}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>


          
          <div className="flex items-center gap-6">
            <button className="relative p-2 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-all">
              <Bell className="w-5 h-5" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-blue-500 rounded-full border-2 border-slate-950"></span>
            </button>
            <div className="h-6 w-px bg-white/10"></div>
            <UserProfile />
          </div>
        </header>

        <div className="flex-1 overflow-auto relative">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default DashboardLayout;
