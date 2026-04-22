import { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, Plus, MessageSquare, Menu, X, FileText, Link, Check, ExternalLink, ChevronDown, Zap, Sparkles } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';

function Chat() {
  const location = useLocation();
  const navigate = useNavigate();
  // We manage sessionId in state so we can change it without unmounting the whole component
  const currentSessionId = location.state?.sessionId || sessionStorage.getItem('last_session_id');
  const [sessionId, setSessionId] = useState(currentSessionId);

  const [messages, setMessages] = useState([
    { role: 'assistant', content: '안녕하세요! 분석된 코드에 대해 무엇이든 물어보세요.' }
  ]);
  const [sessions, setSessions] = useState([]);
  const [currentProjectId, setCurrentProjectId] = useState(null);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [provider, setProvider] = useState('groq');
  const [modelName, setModelName] = useState('llama-3.3-70b-versatile');
  const [isModelMenuOpen, setIsModelMenuOpen] = useState(false);
  const messagesEndRef = useRef(null);

  const models = {
    groq: [
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B', desc: 'Fast & Versatile' },
      { id: 'llama-3.1-70b-versatile', name: 'Llama 3.1 70B', desc: 'Large Context' },
      { id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B', desc: 'Ultra Fast' }
    ],
    openai: [
      { id: 'gpt-4o-mini', name: 'GPT-4o Mini', desc: 'Smarter & Precise' },
      { id: 'gpt-4o', name: 'GPT-4o (Pro)', desc: 'High Quality AI' }
    ]
  };


  useEffect(() => {
    if (currentSessionId && currentSessionId !== sessionId) {
      setSessionId(currentSessionId);
    }
  }, [currentSessionId]);

  useEffect(() => {
    if (!sessionId) {
      alert("유효한 세션이 없습니다. 분석을 먼저 진행해주세요.");
      navigate('/');
    }
  }, [sessionId, navigate]);

  const loadSessionData = async (sid) => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      // 1. Get session info
      const infoRes = await fetch(`http://localhost:8000/chat/session/${sid}/info`, { headers });
      if (!infoRes.ok) throw new Error('세션 정보를 불러오지 못했습니다.');
      const infoData = await infoRes.json();
      setCurrentProjectId(infoData.project_id);

      // 2. Get history
      const histRes = await fetch(`http://localhost:8000/chat/history/${sid}`, { headers });
      if (histRes.ok) {
        const histData = await histRes.json();
        if (histData.length > 0) {
          setMessages(histData);
        } else {
          setMessages([{ role: 'assistant', content: '안녕하세요! 분석된 코드에 대해 무엇이든 물어보세요.' }]);
        }
      }

      // 3. Get sibling sessions
      if (infoData.project_id) {
        const siblingRes = await fetch(`http://localhost:8000/chat/sessions/${infoData.project_id}`, { headers });
        if (siblingRes.ok) {
          const siblingData = await siblingRes.json();
          setSessions(siblingData);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (sessionId) {
      loadSessionData(sessionId);
    }
  }, [sessionId]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleNewSession = async () => {
    if (!currentProjectId) return;
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');

      const response = await fetch('http://localhost:8000/chat/session/new', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
          project_id: currentProjectId,
          provider: provider,
          model_name: modelName
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        navigate('.', { state: { ...location.state, sessionId: data.session_id }, replace: true });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !sessionId) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      // FastAPI 백엔드 호출
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          session_id: sessionId, 
          query: input,
          provider: provider,
          model_name: modelName
        })
      });

      if (!response.ok) {
        throw new Error('대화 중 오류가 발생했습니다.');
      }


      const data = await response.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.answer,
        sources: data.sources,
        graph_trace: data.graph_trace
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: '죄송합니다. 오류가 발생했습니다: ' + err.message }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar for Chat History */}
      <div className={`${isSidebarOpen ? 'w-64 translate-x-0' : 'w-0 -translate-x-full'} transition-all duration-300 ease-in-out shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col z-20 absolute lg:relative h-full lg:h-auto`}>
        <div className="p-4 border-b border-slate-800 flex justify-between items-center">
          <button 
            onClick={handleNewSession}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-transparent border border-slate-700 hover:bg-slate-800 text-slate-200 rounded-xl transition-all font-medium text-sm disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            새 대화 시작
          </button>
          <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden ml-2 p-2 text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Model Selector in Sidebar */}
        <div className="p-4 border-b border-slate-800">
          <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3 px-1">AI Engine</div>
          <div className="relative">
            <button 
              onClick={() => setIsModelMenuOpen(!isModelMenuOpen)}
              className="w-full flex items-center justify-between p-3 bg-slate-800/50 border border-slate-700/50 rounded-xl hover:bg-slate-800 transition-all group"
            >
              <div className="flex items-center gap-3">
                <div className={`p-1.5 rounded-lg ${provider === 'openai' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}`}>
                  {provider === 'openai' ? <Sparkles size={14} /> : <Zap size={14} />}
                </div>
                <div className="text-left">
                  <div className="text-xs font-bold text-slate-200">{models[provider].find(m => m.id === modelName)?.name}</div>
                  <div className="text-[10px] text-slate-500">{provider === 'openai' ? 'OpenAI Pro' : 'Groq Free'}</div>
                </div>
              </div>
              <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${isModelMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {isModelMenuOpen && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-200">
                <div className="p-2 border-b border-slate-800 flex gap-1">
                  {['groq', 'openai'].map(p => (
                    <button
                      key={p}
                      onClick={(e) => { e.stopPropagation(); setProvider(p); setModelName(models[p][0].id); }}
                      className={`flex-1 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all ${provider === p ? 'bg-blue-600 text-white' : 'text-slate-500 hover:bg-slate-800'}`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
                <div className="max-h-48 overflow-y-auto custom-scrollbar p-1">
                  {models[provider].map(m => (
                    <button
                      key={m.id}
                      onClick={(e) => { e.stopPropagation(); setModelName(m.id); setIsModelMenuOpen(false); }}
                      className={`w-full text-left p-2.5 rounded-xl transition-all flex items-center justify-between group ${modelName === m.id ? 'bg-blue-600/10' : 'hover:bg-slate-800'}`}
                    >
                      <div>
                        <div className={`text-xs font-bold ${modelName === m.id ? 'text-blue-400' : 'text-slate-300'}`}>{m.name}</div>
                        <div className="text-[10px] text-slate-500">{m.desc}</div>
                      </div>
                      {modelName === m.id && <Check size={12} className="text-blue-400" />}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
          <div className="text-xs font-black text-slate-500 uppercase px-3 py-2 tracking-widest">
            Recent Chats
          </div>
          {sessions.map((s) => (
            <button
              key={s.session_id}
              onClick={() => {
                setSessionId(s.session_id);
                navigate('.', { state: { ...location.state, sessionId: s.session_id }, replace: true });
                if (window.innerWidth < 1024) setIsSidebarOpen(false);
              }}
              className={`w-full text-left px-3 py-3 rounded-xl flex items-start gap-3 transition-colors ${
                s.session_id === sessionId 
                  ? 'bg-blue-600/10 text-blue-400' 
                  : 'hover:bg-slate-800/50 text-slate-400 hover:text-slate-200'
              }`}
            >
              <MessageSquare className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="overflow-hidden">
                <div className="text-sm truncate font-medium">Chat Session</div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {new Date(s.created_at).toLocaleDateString()}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative w-full h-full min-w-0">
        {/* Background Decorative Elements */}
        <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/5 blur-[120px] rounded-full pointer-events-none"></div>

        {/* Mobile Header for Sidebar Toggle */}
        <div className="lg:hidden p-4 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md flex items-center gap-3 relative z-10">
          <button onClick={() => setIsSidebarOpen(true)} className="p-2 -ml-2 text-slate-400 hover:text-white">
            <Menu className="w-5 h-5" />
          </button>
          <span className="font-bold text-slate-200">ChatFolio AI</span>
        </div>

        {/* 메시지 영역 */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 relative z-10 custom-scrollbar scroll-smooth">
        {messages.map((msg, idx) => (
          <div 
            key={idx} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex gap-3 max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-md ${
                msg.role === 'user' ? 'bg-blue-600' : 'bg-purple-600'
              }`}>
                {msg.role === 'user' ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
              </div>
              <div className={`p-4 rounded-2xl shadow-md text-sm leading-relaxed ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-none' 
                  : 'bg-slate-800/80 backdrop-blur-sm text-slate-200 border border-slate-700/50 rounded-tl-none'
              }`}>
                {msg.content}
                
                {msg.sources && msg.sources.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="flex items-center gap-1.5 text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">
                      <Link className="w-3 h-3" /> References
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {msg.sources.map((src, sidx) => (
                        <div 
                          key={sidx}
                          className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-900/50 border border-slate-700/50 rounded-lg text-[11px] text-slate-400 hover:text-blue-400 hover:border-blue-500/30 transition-all cursor-default group"
                        >
                          <FileText className="w-3 h-3 text-slate-500 group-hover:text-blue-400" />
                          <span className="max-w-[120px] truncate">{src.path.split('/').pop()}</span>
                          <span className="text-[9px] px-1 bg-slate-800 rounded text-slate-600 group-hover:text-blue-500/50">{src.reason === 'Vector Similarity' ? 'RAG' : 'Graph'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center shrink-0 shadow-md">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-slate-800/80 backdrop-blur-sm p-4 rounded-2xl shadow-md border border-slate-700/50 rounded-tl-none">
                <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* 입력 영역 */}
      <footer className="bg-slate-900/80 backdrop-blur-md border-t border-slate-800 p-4 pb-8 relative z-10">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto relative">
          <input
            type="text"
            className="w-full p-4 pr-14 border border-slate-700 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-slate-800 text-slate-100 placeholder-slate-500"
            placeholder="코드의 구조나 특정 기능에 대해 물어보세요..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute right-2 top-2 p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </footer>
      </div>
    </div>
  );
}


export default Chat;
