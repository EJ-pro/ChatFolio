import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { FileText, Loader2, Copy, Sparkles, CheckCircle2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

function DocsTab() {
  const location = useLocation();
  const sessionId = location.state?.sessionId;
  
  const [readmeContent, setReadmeContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const handleGenerateReadme = async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    setError('');
    setReadmeContent('');
    setCopied(false);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/generate/readme', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ session_id: sessionId })
      });

      if (!response.ok) {
        throw new Error('README 생성 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setReadmeContent(data.readme_content);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(readmeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex h-full bg-slate-50">
      {/* Left Panel: Controls */}
      <div className="w-1/3 min-w-[350px] p-8 bg-white border-r border-slate-200 overflow-y-auto">
        <header className="mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-sm font-bold mb-4">
            <Sparkles className="w-4 h-4" />
            <span>AI Auto-Docs</span>
          </div>
          <h2 className="text-3xl font-bold text-slate-900 mb-2">문서 자동화</h2>
          <p className="text-slate-500 text-sm">프로젝트 아키텍처와 핵심 코드를 분석하여 고품질의 문서를 생성합니다.</p>
        </header>

        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 shadow-sm">
          <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center mb-4">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2">README 생성기</h3>
          <p className="text-slate-600 text-sm mb-6 leading-relaxed">
            전체 파일 개수, 가장 많이 참조된 핵심 파일 Top 5, 그리고 디렉토리 구조를 바탕으로 Github에 올릴 수 있는 README.md를 자동 작성합니다.
          </p>
          
          <button
            onClick={handleGenerateReadme}
            disabled={isLoading || !sessionId}
            className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-bold shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>README 생성 중...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>README 자동 생성 🚀</span>
              </>
            )}
          </button>

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-100 text-red-600 text-sm rounded-lg text-center font-medium">
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel: Viewer */}
      <div className="flex-1 bg-slate-900 overflow-hidden flex flex-col relative">
        {readmeContent ? (
          <>
            <div className="absolute top-4 right-4 z-10">
              <button
                onClick={copyToClipboard}
                className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg backdrop-blur-sm border border-white/10 transition-colors shadow-lg"
              >
                {copied ? <CheckCircle2 className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                <span className="font-medium text-sm">{copied ? '복사 완료!' : '📋 Markdown 복사'}</span>
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-10 custom-scrollbar">
              <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-2xl overflow-hidden min-h-full">
                {/* GitHub Style Header */}
                <div className="bg-slate-100 border-b border-slate-200 px-6 py-3 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-500" />
                  <span className="text-sm font-semibold text-slate-700">README.md</span>
                </div>
                
                {/* Markdown Content */}
                <div className="p-8 prose prose-slate max-w-none prose-headings:font-bold prose-a:text-blue-600 prose-pre:bg-slate-800 prose-pre:text-slate-100">
                  <ReactMarkdown>{readmeContent}</ReactMarkdown>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-slate-500">
            {isLoading ? (
              <div className="flex flex-col items-center">
                <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                <p className="text-slate-400 font-medium text-lg">AI가 아키텍처를 분석하여 README를 작성하고 있습니다...</p>
                <p className="text-slate-500 text-sm mt-2">이 작업은 약 10~20초 정도 소요됩니다.</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 bg-slate-800 rounded-full flex items-center justify-center mb-6 border border-slate-700">
                  <FileText className="w-10 h-10 text-slate-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-300 mb-2">생성된 문서가 없습니다</h3>
                <p className="text-slate-500">좌측의 생성 버튼을 눌러 프로젝트 README를 만들어보세요.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default DocsTab;
