import { FileText, Briefcase, GitGraph, Hammer, Copy } from 'lucide-react';

function DocsTab() {
  const docsOptions = [
    {
      id: 'readme',
      title: 'README 생성기',
      description: '핵심 파일과 의존성 그래프를 바탕으로 Github용 마크다운 README를 자동 작성합니다.',
      icon: FileText,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50',
      prompt: '이 프로젝트의 핵심 파일과 의존성 그래프를 바탕으로, Github에 바로 올릴 수 있는 마크다운 형식의 README를 작성해줘.'
    },
    {
      id: 'portfolio',
      title: '이력서 문장 추출',
      description: 'STAR 기법을 적용하여 이력서에 바로 들어갈 성과 중심 문장을 뽑아냅니다.',
      icon: Briefcase,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-50',
      prompt: "이력서에 들어갈 성과 중심의 문장 3줄을 뽑아줘. 'STAR 기법'을 적용해서 핵심 로직을 근거로 작성해."
    },
    {
      id: 'diagram',
      title: 'Mermaid 다이어그램',
      description: '의존성 그래프를 시각화할 수 있는 Mermaid.js 코드를 생성합니다.',
      icon: GitGraph,
      color: 'text-purple-500',
      bgColor: 'bg-purple-50',
      prompt: '현재 수집된 의존성 그래프를 바탕으로, 프로젝트 아키텍처를 보여주는 Mermaid.js 코드를 생성해줘.'
    }
  ];

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto">
        <header className="mb-10">
          <h2 className="text-3xl font-bold text-slate-800 mb-2">문서 자동화</h2>
          <p className="text-slate-500">클릭 한 번으로 프로젝트 문서와 다이어그램을 뽑아보세요.</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {docsOptions.map((option) => (
            <div key={option.id} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow relative overflow-hidden group">
              {/* 개발 중 배지 */}
              <div className="absolute top-4 right-4 bg-amber-100 text-amber-700 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-sm">
                <Hammer className="w-3 h-3" />
                <span>개발 중</span>
              </div>

              <div className={`w-14 h-14 ${option.bgColor} rounded-xl flex items-center justify-center mb-6`}>
                <option.icon className={`w-7 h-7 ${option.color}`} />
              </div>

              <h3 className="text-xl font-bold text-slate-800 mb-3">{option.title}</h3>
              <p className="text-slate-600 text-sm mb-6 leading-relaxed min-h-[60px]">
                {option.description}
              </p>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 mb-6">
                <div className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">AI 프롬프트 예시</div>
                <p className="text-sm text-slate-700 italic line-clamp-3">"{option.prompt}"</p>
              </div>

              <button 
                disabled
                className="w-full flex items-center justify-center gap-2 py-3 bg-slate-100 text-slate-400 rounded-xl font-semibold opacity-70 cursor-not-allowed border border-slate-200"
              >
                <Copy className="w-4 h-4" />
                <span>결과 생성 및 복사</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default DocsTab;
