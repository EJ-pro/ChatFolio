import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Search, Github, Loader2, GitBranch, FileCode2, Share2, Sparkles, MessageSquare, BookOpen, Layers } from 'lucide-react';
import UserProfile from '../components/UserProfile';

function Analysis() {
  const { username } = useParams();
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [provider, setProvider] = useState('groq');
  const [modelName, setModelName] = useState('llama-3.3-70b-versatile');
  const [logs, setLogs] = useState([]);
  const [currentLog, setCurrentLog] = useState('');
  const [projects, setProjects] = useState([]);
  const [searchParams] = useSearchParams();
  const [progress, setProgress] = useState(0);


  useEffect(() => {
    fetchProjects();
    const repoUrl = searchParams.get('repo_url');
    const forceUpdate = searchParams.get('force_update') === 'true';
    if (repoUrl) {
      setUrl(repoUrl);
      if (forceUpdate) {
        // use setTimeout to ensure setUrl is processed or just pass it directly
        handleAnalyze(null, repoUrl, forceUpdate);
      }
    }
  }, [searchParams]);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/projects', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      }
    } catch (err) {
      console.error('Failed to fetch projects:', err);
    }
  };

  const handleAnalyze = async (e, overrideUrl = null, forceUpdate = false) => {
    if (e) e.preventDefault();
    const targetUrl = overrideUrl || url;
    if (!targetUrl) return;

    setIsLoading(true);
    setError('');
    setResult(null);
    setLogs([]);
    setCurrentLog('분석 시작 중...');
    setProgress(0);


    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          repo_url: targetUrl,
          provider: provider,
          model_name: modelName,
          force_update: forceUpdate
        })
      });

      if (response.status === 401 || response.status === 403 || response.status === 404) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const msg = line.replace('data: ', '').trim();

            if (msg.startsWith('RESULT:')) {
              const resultData = JSON.parse(msg.replace('RESULT:', ''));
              setResult(resultData);
              setIsLoading(false);
              return;
            } else if (msg.startsWith('ERROR:')) {
              throw new Error(msg.replace('ERROR:', ''));
            } else if (msg.startsWith('PROGRESS:')) {
              setProgress(parseInt(msg.replace('PROGRESS:', '')));
            } else {
              setCurrentLog(msg);
              setLogs(prev => [...prev.slice(-4), msg]); // 최근 5개 로그 유지
            }

          }
        }
      }
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col relative overflow-hidden font-sans">
      {/* Background Decorative Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 blur-[120px] rounded-full pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 blur-[120px] rounded-full pointer-events-none"></div>

      {/* Top Header */}
      <header className="w-full px-8 py-4 flex justify-between items-center sticky top-0 z-50 backdrop-blur-md border-b border-white/5 bg-slate-900/50">
        <button
          onClick={() => navigate(`/${username}`)}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-all group"
        >
          <Github className="w-6 h-6 group-hover:rotate-12 transition-transform" />
          <span className="font-black tracking-tighter text-xl text-white">ChatFolio</span>
        </button>
        <UserProfile />
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 relative z-10 w-full max-w-5xl mx-auto mt-10">

        {/* Hero Section */}
        <div className="text-center mb-12 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700/50 text-blue-400 text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            <span>ChatFolio AI Beta</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
            당신의 코드와<br />대화를 시작하세요.
          </h1>
          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            복잡한 레포지토리의 의존성을 시각화하고, AI와 대화하며 코드에 대해 깊이 알아보세요.
          </p>
        </div>

        {/* Model Selector */}
        <div className="flex items-center justify-center gap-4 mb-10 animate-fade-in-up delay-100">
          <div className="flex bg-slate-900/50 p-1 rounded-2xl border border-white/10 backdrop-blur-md shadow-inner">
            <button
              onClick={() => { setProvider('groq'); setModelName('llama-3.3-70b-versatile'); }}
              className={`px-6 py-2 rounded-xl text-sm font-bold transition-all duration-300 ${provider === 'groq' ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
            >
              Groq (Free)
            </button>
            <button
              onClick={() => { setProvider('openai'); setModelName('gpt-4o-mini'); }}
              className={`px-6 py-2 rounded-xl text-sm font-bold transition-all duration-300 ${provider === 'openai' ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:text-white'}`}
            >
              OpenAI (Paid)
            </button>
          </div>
        </div>

        {/* Search Section */}
        <div className="w-full max-w-3xl animate-fade-in-up delay-100">
          <form onSubmit={handleAnalyze} className="relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-500"></div>
            <div className="relative flex items-center glass-panel rounded-2xl p-2 shadow-2xl bg-slate-950/50 border border-slate-700/50">
              <div className="pl-4 flex items-center pointer-events-none">
                <Search className="h-6 w-6 text-slate-400 group-focus-within:text-blue-400 transition-colors" />
              </div>
              <input
                type="text"
                className="w-full pl-4 pr-32 py-4 bg-transparent border-none text-white placeholder-slate-400 focus:outline-none focus:ring-0 text-lg font-medium"
                placeholder="https://github.com/username/repository"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !url}
                className="absolute right-3 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl font-bold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all transform active:scale-95"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-5 h-5 animate-spin" /> 분석 중
                  </span>
                ) : (
                  '분석 시작'
                )}
              </button>
            </div>
          </form>

          {/* Integrated Recent Projects */}
          {projects.length > 0 && !result && !error && !isLoading && (
            <div className="mt-6 animate-fade-in">
              <div className="flex items-center gap-2 mb-3 px-1">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">최근 분석 기록</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {projects.slice(0, 5).map((project) => (
                  <button
                    key={project.id}
                    onClick={() => {
                      setUrl(project.repo_url);
                      // 즉시 분석 시작 효과를 위해 폼 제출 시뮬레이션
                    }}
                    className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/50 border border-white/5 rounded-xl hover:border-blue-500/50 hover:bg-blue-500/5 transition-all group"
                  >
                    <Github className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400" />
                    <span className="text-xs font-medium text-slate-400 group-hover:text-white truncate max-w-[150px]">
                      {project.repo_url.split('/').slice(-1)}
                    </span>
                  </button>
                ))}
                <button
                  onClick={() => navigate(`/${username}`)}
                  className="px-3 py-1.5 text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors"
                >
                  모두 보기
                </button>
              </div>
            </div>
          )}

          {/* Analysis Progress Logs */}
          {isLoading && (
            <div className="mt-8 w-full animate-fade-in">
              <div className="bg-slate-950/80 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl">
                {/* Progress Bar */}
                <div className="h-1 w-full bg-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-blue-600 to-indigo-500 shadow-[0_0_10px_rgba(37,99,235,0.5)] transition-all duration-500 ease-out"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <div className="px-4 py-2 bg-slate-900/50 border-b border-slate-800 flex items-center justify-between">

                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest flex items-center gap-2">
                    Analysis Engine Terminal
                    <span className="text-blue-400 font-bold">[{progress}%]</span>
                  </span>
                </div>
                <div className="p-6 font-mono text-sm space-y-2">
                  <div className="flex items-center gap-3 text-blue-400">
                    <span className="shrink-0 opacity-50">➜</span>
                    <span className="font-bold animate-pulse">{currentLog}</span>
                  </div>
                  <div className="space-y-1 opacity-40">
                    {logs.map((log, i) => (
                      <div key={i} className="flex items-center gap-3 text-slate-300">
                        <span className="shrink-0 opacity-30">#</span>
                        <span className="truncate">{log}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}


          {/* Quick Try Buttons */}
          {!result && !error && !isLoading && (
            <div className="flex items-center justify-center gap-3 mt-6 text-sm text-slate-300 font-medium animate-fade-in delay-300">
              <span>Try with:</span>
              <button onClick={() => setUrl('https://github.com/square/okhttp')} className="px-3 py-1 rounded-full bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-600 text-white">square/okhttp</button>
              <button onClick={() => setUrl('https://github.com/JetBrains/kotlin')} className="px-3 py-1 rounded-full bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-600 text-white">JetBrains/kotlin</button>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-8 p-4 bg-red-900/40 border border-red-500/50 text-red-100 rounded-xl max-w-2xl w-full text-center animate-fade-in font-medium">
            {error}
          </div>
        )}

        {/* Result Card */}
        {result && (
          <div className="mt-12 w-full max-w-3xl glass-panel rounded-3xl p-8 animate-fade-in-up shadow-2xl border border-white/10 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-blue-500"></div>

            <div className="text-center mb-10">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-500/10 text-emerald-400 mb-6 border border-emerald-500/20">
                <Sparkles className="w-10 h-10" />
              </div>
              <h3 className="text-3xl font-bold text-white mb-3 tracking-tight">{result.message}</h3>
              <p className="text-slate-300 text-lg">성공적으로 레포지토리 구조를 파악했습니다.</p>
            </div>

            <div className="grid grid-cols-3 gap-6 mb-10">
              <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/5 flex flex-col items-center justify-center text-center group hover:bg-slate-800 transition-all duration-300 hover:border-white/10 shadow-inner">
                <FileCode2 className="w-10 h-10 text-blue-400 mb-4 group-hover:scale-110 transition-transform" />
                <span className="text-4xl font-black text-white mb-1 tracking-tighter">{result.file_count}</span>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Kotlin Files</span>
              </div>
              <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/5 flex flex-col items-center justify-center text-center group hover:bg-slate-800 transition-all duration-300 hover:border-white/10 shadow-inner">
                <Layers className="w-10 h-10 text-emerald-400 mb-4 group-hover:scale-110 transition-transform" />
                <span className="text-4xl font-black text-white mb-1 tracking-tighter">{result.node_count}</span>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Classes/Funcs</span>
              </div>
              <div className="bg-slate-900/50 p-6 rounded-2xl border border-white/5 flex flex-col items-center justify-center text-center group hover:bg-slate-800 transition-all duration-300 hover:border-white/10 shadow-inner">
                <GitBranch className="w-10 h-10 text-purple-400 mb-4 group-hover:scale-110 transition-transform" />
                <span className="text-4xl font-black text-white mb-1 tracking-tighter">{result.edge_count}</span>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Dependencies</span>
              </div>
            </div>

            <button
              className="w-full py-5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-2xl font-black text-xl shadow-[0_0_30px_rgba(79,70,229,0.4)] transition-all transform hover:-translate-y-1 hover:shadow-[0_0_40px_rgba(79,70,229,0.5)] active:scale-95"
              onClick={() => navigate(`/${username}/dashboard/chat`, { state: { sessionId: result.session_id } })}
            >
              대시보드 입장하기 ✨
            </button>
          </div>
        )}

        {/* Features Section (Only show when not loading and no result) */}
        {!isLoading && !result && !error && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl mt-24 animate-fade-in-up delay-400">
            <div className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/30 hover:bg-slate-800/50 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-4 text-blue-400">
                <GitBranch className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">의존성 그래프 분석</h3>
              <p className="text-slate-400 text-sm leading-relaxed">복잡하게 얽힌 클래스와 함수 간의 호출 관계를 시각적으로 분석하여 전체 아키텍처를 빠르게 파악합니다.</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/30 hover:bg-slate-800/50 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-4 text-purple-400">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">컨텍스트 AI 대화</h3>
              <p className="text-slate-400 text-sm leading-relaxed">단순한 코드 검색을 넘어, 프로젝트의 맥락을 완벽히 이해한 AI와 심도 깊은 기술적 대화를 나눌 수 있습니다.</p>
            </div>
            <div className="p-6 rounded-2xl bg-slate-800/30 border border-slate-700/30 hover:bg-slate-800/50 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center mb-4 text-emerald-400">
                <BookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">자동화된 문서화</h3>
              <p className="text-slate-400 text-sm leading-relaxed">README 작성, 포트폴리오 성과 요약, 면접 대비용 압박 질문까지 AI가 자동으로 생성해 드립니다.</p>
            </div>
          </div>
        )}

      </main>

      <footer className="w-full text-center p-6 text-slate-500 text-sm animate-fade-in delay-500 relative z-10">
        &copy; 2026 ChatFolio. Designed for developers.
      </footer>
    </div>
  );
}

export default Analysis;