import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, HelpCircle, ChevronDown, ChevronUp, Mail, Phone, User, Github } from 'lucide-react';
import UserProfile from '../components/UserProfile';

function FAQ() {
  const navigate = useNavigate();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const [openId, setOpenId] = useState(null);
  const [activeTab, setActiveTab] = useState('faq'); // 'faq' or 'inquiry'
  const [inquiryData, setInquiryData] = useState({ title: '', content: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const faqs = [
    {
      id: 1,
      question: "ChatFolio는 어떤 서비스인가요?",
      answer: "ChatFolio는 GitHub 레포지토리를 분석하여 의존성 그래프를 시각화하고, AI와 대화하며 코드를 심층 분석할 수 있는 개발자용 포트폴리오 최적화 도구입니다."
    },
    {
      id: 2,
      question: "프라이빗 레포지토리도 분석이 가능한가요?",
      answer: "네, GitHub 로그인 시 'repo' 권한을 승인해 주시면 본인의 프라이빗 레포지토리도 안전하게 읽어와 분석할 수 있습니다."
    },
    {
      id: 3,
      question: "분석된 데이터는 어떻게 관리되나요?",
      answer: "수집된 코드는 분석 및 AI 컨텍스트 구성 용도로만 사용되며, 이용자가 삭제를 요청하거나 연동을 해제할 경우 즉시 파기됩니다."
    },
    {
      id: 4,
      question: "MBTI 페르소나 분석은 어떤 기준인가요?",
      answer: "사용자의 커밋 빈도, 주로 사용하는 기술 스택, 코드 스타일(주석 사용, 모듈화 정도) 등을 종합적으로 분석하여 AI가 가장 가까운 개발자 유형을 정의합니다."
    }
  ];

  const handleInquirySubmit = async (e) => {
    e.preventDefault();
    if (!inquiryData.title || !inquiryData.content) {
      alert('제목과 내용을 모두 입력해주세요.');
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/inquiries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(inquiryData)
      });

      if (response.ok) {
        alert('문의가 정상적으로 접수되었습니다.');
        setInquiryData({ title: '', content: '' });
        setActiveTab('faq');
      } else {
        const data = await response.json();
        alert(data.detail || '문의 제출 중 오류가 발생했습니다.');
      }
    } catch (err) {
      console.error('Failed to submit inquiry:', err);
      alert('서버와 통신 중 오류가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

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
        <div className="text-center mb-12">
          <h1 className="text-5xl font-black text-white mb-4 tracking-tighter italic">Customer Center</h1>
          <p className="text-slate-400 text-lg">무엇을 도와드릴까요?</p>
        </div>

        {/* Tab Toggle */}
        <div className="flex justify-center mb-10">
          <div className="bg-slate-900/80 p-1.5 rounded-2xl border border-white/5 flex gap-1">
            <button
              onClick={() => setActiveTab('faq')}
              className={`px-8 py-2.5 rounded-xl font-bold transition-all ${activeTab === 'faq' ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'text-slate-500 hover:text-slate-300'}`}
            >
              자주 묻는 질문 (FAQ)
            </button>
            <button
              onClick={() => setActiveTab('inquiry')}
              className={`px-8 py-2.5 rounded-xl font-bold transition-all ${activeTab === 'inquiry' ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20' : 'text-slate-500 hover:text-slate-300'}`}
            >
              1:1 문의하기
            </button>
          </div>
        </div>

        <div className="min-h-[400px]">
          {activeTab === 'faq' ? (
            <section className="space-y-4 animate-fade-in">
              {faqs.map((faq) => (
                <div
                  key={faq.id}
                  className="glass-panel rounded-2xl border border-white/5 overflow-hidden transition-all hover:border-white/10"
                >
                  <button
                    onClick={() => setOpenId(openId === faq.id ? null : faq.id)}
                    className="w-full p-6 flex justify-between items-center text-left"
                  >
                    <span className="text-lg font-bold text-white flex items-center gap-3">
                      <HelpCircle className="w-5 h-5 text-blue-400" />
                      {faq.question}
                    </span>
                    {openId === faq.id ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </button>
                  {openId === faq.id && (
                    <div className="px-6 pb-6 text-slate-400 leading-relaxed animate-fade-in">
                      <div className="pt-4 border-t border-white/5">
                        {faq.answer}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </section>
          ) : (
            <section className="animate-fade-in">
              <form onSubmit={handleInquirySubmit} className="glass-panel rounded-3xl p-8 md:p-10 border border-white/10 space-y-6">
                <div className="space-y-2">
                  <label className="text-sm font-black text-slate-500 uppercase tracking-widest ml-1">문의 제목</label>
                  <input
                    type="text"
                    placeholder="제목을 입력해주세요"
                    value={inquiryData.title}
                    onChange={(e) => setInquiryData({ ...inquiryData, title: e.target.value })}
                    className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-purple-500/50 transition-colors"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-black text-slate-500 uppercase tracking-widest ml-1">문의 내용</label>
                  <textarea
                    placeholder="궁금한 내용을 상세히 적어주시면 빠른 시일 내에 답변 드리겠습니다."
                    rows={8}
                    value={inquiryData.content}
                    onChange={(e) => setInquiryData({ ...inquiryData, content: e.target.value })}
                    className="w-full bg-slate-950 border border-white/10 rounded-2xl px-6 py-4 text-white focus:outline-none focus:border-purple-500/50 transition-colors resize-none"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-black text-lg rounded-2xl shadow-xl shadow-purple-500/20 transition-all transform hover:-translate-y-1 active:scale-95 disabled:opacity-50"
                >
                  {isSubmitting ? '제출 중...' : '문의 제출하기'}
                </button>
              </form>
            </section>
          )}
        </div>

        {/* Bottom Contact Info */}
        <div className="mt-20 py-10 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6 text-slate-500">
          <div className="flex flex-wrap justify-center gap-8 text-sm font-bold">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-blue-400" />
              <span>대표 : 이재희</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="w-4 h-4 text-emerald-400" />
              <span>TEL : 02-529-4237</span>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-purple-400" />
              <span>Mail : ChatFolio@chatfolio.com</span>
            </div>
          </div>
          <div className="text-[10px] uppercase font-black tracking-widest opacity-30">
            Powered by ChatFolio AI
          </div>
        </div>
      </main>

      <footer className="w-full text-center p-4 text-slate-600 text-sm border-t border-white/5">
        &copy; 2026 ChatFolio. All rights reserved.
      </footer>
    </div>
  );
}

export default FAQ;
