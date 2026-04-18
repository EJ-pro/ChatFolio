import { Target, User, Send, Flame, ShieldAlert } from 'lucide-react';

function InterviewTab() {
  return (
    <div className="flex flex-col h-full bg-slate-900">
      {/* 인터뷰 전용 다크 헤더 */}
      <header className="bg-slate-950 border-b border-slate-800 p-6 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-red-500/10 rounded-xl flex items-center justify-center border border-red-500/20">
            <Flame className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h2 className="font-bold text-white text-xl">하드코어 모의 면접</h2>
            <p className="text-sm text-slate-400">10년 차 안드로이드 시니어 개발자의 압박 면접</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 bg-amber-500/10 text-amber-500 px-4 py-2 rounded-full border border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.15)]">
          <ShieldAlert className="w-4 h-4" />
          <span className="text-sm font-bold tracking-wide">개발 중 (Under Construction)</span>
        </div>
      </header>

      {/* 대화 영역 (Mock) */}
      <main className="flex-1 overflow-y-auto p-8 space-y-6">
        <div className="flex justify-start">
          <div className="flex gap-4 max-w-[80%]">
            <div className="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center shrink-0 shadow-lg shadow-red-900/50">
              <Flame className="w-6 h-6 text-white" />
            </div>
            <div className="bg-slate-800 text-slate-200 p-5 rounded-2xl rounded-tl-none border border-slate-700 shadow-md">
              <p className="leading-relaxed">
                반갑습니다. 제출하신 <code className="bg-slate-900 px-2 py-1 rounded text-red-400 font-mono text-sm">AppContainer.kt</code> 코드를 잘 봤습니다. 
                <br/><br/>
                의존성 주입을 수동으로 구성하셨던데, 만약 프로젝트 규모가 커져서 싱글톤 객체가 수백 개로 늘어난다면 메모리 누수나 초기화 순서 문제는 어떻게 제어하실 계획인가요? Hilt나 Dagger를 쓰지 않은 특별한 이유가 있나요?
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <div className="flex gap-4 max-w-[80%] flex-row-reverse">
            <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center shrink-0 border border-slate-600">
              <User className="w-6 h-6 text-slate-300" />
            </div>
            <div className="bg-blue-600 text-white p-5 rounded-2xl rounded-tr-none shadow-md opacity-50 relative">
              <div className="absolute inset-0 bg-slate-900/40 rounded-2xl rounded-tr-none flex items-center justify-center backdrop-blur-sm z-10">
                <span className="bg-slate-900 px-4 py-2 rounded-lg font-bold text-slate-300 border border-slate-700">기능 준비 중입니다</span>
              </div>
              <p className="leading-relaxed blur-[2px]">
                어... 그 부분은 아직 깊게 고민해보지 못했습니다. 프로젝트 초기 단계라서 당장 복잡한 라이브러리를 도입하기보다는 직관적인 구조를 가져가려고 했습니다...
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* 입력 영역 (비활성화) */}
      <footer className="bg-slate-950 border-t border-slate-800 p-6">
        <div className="max-w-4xl mx-auto relative opacity-50 cursor-not-allowed">
          <input
            type="text"
            disabled
            className="w-full p-4 pr-14 border border-slate-700 rounded-2xl bg-slate-900 text-slate-300 placeholder-slate-600 cursor-not-allowed"
            placeholder="압박 질문에 대한 답변을 입력하세요 (개발 중)..."
          />
          <button
            disabled
            className="absolute right-2 top-2 p-2.5 bg-slate-800 text-slate-500 rounded-xl cursor-not-allowed border border-slate-700"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </footer>
    </div>
  );
}

export default InterviewTab;
