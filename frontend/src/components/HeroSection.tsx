import { Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { getMarketTrends } from '../services/api';
import type { MarketTrend } from '../types';

interface HeroSectionProps {
  onNavigateToList?: (sector?: string) => void;
}

const COLOR_POOL = [
  'from-blue-500 to-cyan-500',
  'from-purple-500 to-pink-500',
  'from-green-500 to-emerald-500',
  'from-amber-500 to-orange-500',
  'from-indigo-500 to-blue-500',
];

export function HeroSection({ onNavigateToList }: HeroSectionProps) {
  const [trend, setTrend] = useState<MarketTrend | null>(null);

  useEffect(() => {
    getMarketTrends()
      .then(setTrend)
      .catch(() => {
        // 실패 시 trend는 null로 남겨둠 (기본 안내 텍스트 사용)
      });
  }, []);

  const risingSectors = useMemo(() => {
    if (!trend?.rising_sectors?.length) return [];
    return trend.rising_sectors.map((sector, idx) => ({
      ...sector,
      color: COLOR_POOL[idx % COLOR_POOL.length],
    }));
  }, [trend]);

  const aiAnalysisText =
    trend?.ai_analysis_text ||
    'AI 분석 결과를 불러오지 못했습니다. 나중에 다시 시도해주세요.';

  return (
    <section className="mb-8">
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-blue-500/20 p-3 rounded-xl">
            <Sparkles className="size-6 text-blue-400" />
          </div>
          <h2 className="text-2xl text-slate-100">AI 시장 인사이트</h2>
        </div>
        
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 mb-6 min-h-[120px]">
          <p className="text-slate-300 leading-relaxed">
            {aiAnalysisText}
          </p>
        </div>
        
        <div>
          <p className="text-sm text-slate-400 mb-3">상승 섹터</p>
          <div className="flex flex-wrap gap-3">
            {risingSectors.length === 0 && (
              <span className="text-xs text-slate-500">데이터 없음</span>
            )}
            {risingSectors.map((sector, index) => (
              <button
                key={index}
                onClick={() => onNavigateToList && onNavigateToList(sector.name)}
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