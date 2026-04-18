import { useState } from 'react';
import { Search, Github, Loader2, GitBranch, FileCode2, Share2 } from 'lucide-react';

function App() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!url) return;

    setIsLoading(true);
    setError('');
    setResult(null);

    try {
      // FastAPI 백엔드 호출
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: url })
      });

      if (!response.ok) {
        throw new Error('분석 중 오류가 발생했습니다. URL을 확인해주세요.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col items-center justify-center p-4">

      {/* 헤더 섹션 */}
      <div className="text-center mb-10">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Github className="w-12 h-12 text-slate-700" />
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">ChatFolio</h1>
        </div>
        <p className="text-lg text-slate-600">당신의 코드가 스스로 말하게 하세요.</p>
      </div>

      {/* 메인 검색 카드 */}
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-100 p-8">
        <form onSubmit={handleAnalyze} className="relative flex items-center">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-slate-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-11 pr-32 py-4 border border-slate-300 rounded-xl leading-5 bg-slate-50 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-lg"
            placeholder="https://github.com/username/repository"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !url}
            className="absolute right-2 px-6 py-2.5 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> 분석 중...
              </span>
            ) : (
              '분석 시작'
            )}
          </button>
        </form>

        {/* 에러 메시지 */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100">
            {error}
          </div>
        )}

        {/* 분석 결과 카드 */}
        {result && (
          <div className="mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h3 className="text-lg font-semibold mb-4 text-slate-800 flex items-center gap-2">
              ✨ {result.message}
            </h3>

            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col items-center justify-center text-center">
                <FileCode2 className="w-6 h-6 text-blue-500 mb-2" />
                <span className="text-2xl font-bold text-slate-800">{result.file_count}</span>
                <span className="text-sm text-slate-500 font-medium">Files</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col items-center justify-center text-center">
                <Share2 className="w-6 h-6 text-emerald-500 mb-2" />
                <span className="text-2xl font-bold text-slate-800">{result.node_count}</span>
                <span className="text-sm text-slate-500 font-medium">Nodes</span>
              </div>
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col items-center justify-center text-center">
                <GitBranch className="w-6 h-6 text-purple-500 mb-2" />
                <span className="text-2xl font-bold text-slate-800">{result.edge_count}</span>
                <span className="text-sm text-slate-500 font-medium">Edges</span>
              </div>
            </div>

            <button
              className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-lg shadow-lg shadow-blue-200 transition-all transform hover:-translate-y-0.5"
              onClick={() => alert('이제 채팅 페이지로 이동하는 로직을 만들 차례입니다!')}
            >
              코드와 대화 시작하기 🚀
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;