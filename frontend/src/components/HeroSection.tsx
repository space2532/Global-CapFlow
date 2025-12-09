import { Sparkles } from 'lucide-react';

const aiAnalysisText = 'AI 분석에 따르면 최근 실적 발표로 인해 반도체 섹터에서 강세 추세가 나타나고 있습니다. 글로벌 수요 증가와 공급망 안정화로 향후 분기에도 긍정적인 전망이 예상됩니다. 특히 AI 칩 제조업체들의 주문량이 전년 대비 45% 증가하며 산업 전반에 활력을 불어넣고 있습니다.';

const risingSectors = [
  { name: 'AI', color: 'from-blue-500 to-cyan-500', sector: '기술' },
  { name: '로보틱스', color: 'from-purple-500 to-pink-500', sector: '산업재' },
  { name: '바이오', color: 'from-green-500 to-emerald-500', sector: '헬스케어' },
  { name: '반도체', color: 'from-amber-500 to-orange-500', sector: '반도체' },
  { name: '클라우드', color: 'from-indigo-500 to-blue-500', sector: '기술' },
];

interface HeroSectionProps {
  onNavigateToList?: (sector?: string) => void;
}

export function HeroSection({ onNavigateToList }: HeroSectionProps) {
  return (
    <section className="mb-8">
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-blue-500/20 p-3 rounded-xl">
            <Sparkles className="size-6 text-blue-400" />
          </div>
          <h2 className="text-2xl text-slate-100">AI 시장 인사이트</h2>
        </div>
        
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6">
          <p className="text-slate-300 leading-relaxed">
            {aiAnalysisText}
          </p>
        </div>
        
        <div>
          <p className="text-sm text-slate-400 mb-3">상승 섹터</p>
          <div className="flex flex-wrap gap-3">
            {risingSectors.map((sector, index) => (
              <button
                key={index}
                onClick={() => onNavigateToList && onNavigateToList(sector.sector)}
                className={`group relative bg-gradient-to-r ${sector.color} px-5 py-2.5 rounded-full text-white shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-200 cursor-pointer overflow-hidden`}
              >
                <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity"></div>
                <div className="relative flex items-center gap-2">
                  <span>{sector.name}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}