import { Globe, TrendingUp, Sparkles, X, Info } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { getMarketTrends } from '../services/api';
import type { MarketTrend } from '../types';

interface SectorBlock {
  name: string;
  percentage: number;
  size: number;
}

interface HeatmapWidgetProps {
  onNavigateToList?: (sector?: string) => void;
}

function getColorClass(percentage: number): string {
  if (percentage >= 25) return 'bg-blue-500 border-blue-400';
  if (percentage >= 18) return 'bg-blue-600 border-blue-500';
  if (percentage >= 12) return 'bg-slate-600 border-slate-500';
  if (percentage >= 8) return 'bg-slate-700 border-slate-600';
  return 'bg-slate-800 border-slate-700';
}

export function HeatmapWidget({ onNavigateToList }: HeatmapWidgetProps) {
  const [selectedSector, setSelectedSector] = useState<SectorBlock | null>(null);
  const [trend, setTrend] = useState<MarketTrend | null>(null);

  useEffect(() => {
    getMarketTrends()
      .then(setTrend)
      .catch(() => {
        // 실패 시 trend는 null로 남김
      });
  }, []);

  const dominantSectors: SectorBlock[] = useMemo(() => {
    if (!trend?.dominant_sectors?.length) return [];
    return trend.dominant_sectors
      .sort((a, b) => b.percentage - a.percentage)
      .map((s, idx) => ({
        name: s.name,
        percentage: s.percentage,
        size: Math.max(1, Math.min(5, Math.round(s.percentage / 6))) + (idx === 0 ? 1 : 0),
      }));
  }, [trend]);

  const risingSectorAnalysis =
    trend?.ai_analysis_text ||
    'AI 분석 결과를 불러오지 못했습니다. 나중에 다시 시도해주세요.';

  const updatedLabel = trend?.date ? `업데이트: ${trend.date}` : '업데이트 정보 없음';

  const handleSectorClick = (sector: SectorBlock) => {
    setSelectedSector(sector);
  };

  const handleNavigate = () => {
    if (selectedSector && onNavigateToList) {
      onNavigateToList(selectedSector.name);
      setSelectedSector(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Heatmap Section */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-4 sm:p-6 shadow-xl">
        <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
          <div className="bg-blue-500/20 p-2 rounded-lg">
            <Globe className="size-4 sm:size-5 text-blue-400" />
          </div>
          <h2 className="text-base sm:text-lg text-slate-200">글로벌 섹터 맵</h2>
          <span className="text-xs text-slate-500 ml-auto hidden sm:inline">탭하여 상세 보기</span>
        </div>
        
        {/* Mobile-Optimized Squarified Treemap */}
        <div className="grid grid-cols-5 gap-2 sm:gap-3 mb-4 sm:mb-6" style={{ minHeight: '320px' }}>
          {dominantSectors.length === 0 && (
            <div className="text-xs text-slate-500 col-span-5">데이터 없음</div>
          )}
          {dominantSectors.map((sector, index) => (
            <button
              key={index}
              onClick={() => handleSectorClick(sector)}
              className={`${getColorClass(sector.percentage)} 
                border-2 rounded-lg sm:rounded-xl p-3 sm:p-4 flex flex-col justify-center items-center text-center
                active:scale-95 sm:hover:scale-105 sm:hover:shadow-2xl sm:hover:brightness-110 transition-all duration-200 cursor-pointer shadow-lg text-white group relative overflow-hidden`}
              style={{ 
                gridColumn: `span ${Math.min(3, Math.max(1, sector.size))}`,
                gridRow: `span ${Math.min(2, Math.max(1, Math.ceil(sector.size / 2)))}`,
                minHeight: `${80 + sector.size * 10}px`
              }}
            >
              {/* Hover/Active overlay */}
              <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-10 group-active:opacity-20 transition-opacity pointer-events-none"></div>
              
              {/* Content - Show text only if block is large enough */}
              <div className="relative flex flex-col justify-center items-center w-full gap-1">
                <span className="text-sm sm:text-base font-semibold tracking-wide" style={{ fontSize: sector.size >= 2 ? '14px' : '12px' }}>
                  {sector.name}
                </span>
                <span className="text-lg sm:text-2xl font-bold opacity-90" style={{ fontSize: sector.size >= 3 ? '24px' : '18px' }}>
                  {sector.percentage}%
                </span>
                {sector.size >= 3 && (
                  <Info className="size-3 sm:size-4 opacity-50 mt-1" />
                )}
              </div>
            </button>
          ))}
        </div>
        
        <div className="flex items-center justify-between text-xs text-slate-400 pt-3 sm:pt-4 border-t border-slate-700">
          <span>시장 점유율 기준</span>
          <span className="hidden sm:inline">실시간 데이터</span>
        </div>
      </div>

      {/* Bottom Sheet Modal for Sector Details */}
      {selectedSector && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end sm:items-center sm:justify-center"
          onClick={() => setSelectedSector(null)}
        >
          <div 
            className="bg-gradient-to-br from-slate-900 to-slate-800 border-t sm:border border-slate-700 rounded-t-3xl sm:rounded-2xl w-full sm:max-w-md sm:mx-4 p-6 shadow-2xl animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setSelectedSector(null)}
              className="absolute top-4 right-4 p-2 rounded-full bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              <X className="size-5 text-slate-400" />
            </button>

            {/* Sector Header */}
            <div className="mb-6">
              <div className={`${getColorClass(selectedSector.percentage)} inline-block px-4 py-1.5 rounded-full text-white text-sm mb-3`}>
                {selectedSector.name}
              </div>
              <h3 className="text-2xl text-slate-100 mb-2">{selectedSector.name}</h3>
              <p className="text-slate-400 text-sm">시장 비중 기반 추정치</p>
            </div>

            {/* Stats */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 mb-6">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">시장 점유율</span>
                <span className="text-3xl text-white font-bold">{selectedSector.percentage}%</span>
              </div>
            </div>

            {/* Action Button */}
            <button
              onClick={handleNavigate}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2"
            >
              <span>상세 목록 보기</span>
              <TrendingUp className="size-5" />
            </button>
          </div>
        </div>
      )}

      {/* Rising Sector AI Analysis Section */}
      <div className="bg-gradient-to-br from-green-900/20 to-emerald-900/10 border border-green-700/30 rounded-2xl p-4 sm:p-6 shadow-xl">
        <div className="flex items-center gap-2 sm:gap-3 mb-4">
          <div className="bg-green-500/20 p-2 rounded-lg">
            <Sparkles className="size-4 sm:size-5 text-green-400" />
          </div>
          <h2 className="text-base sm:text-lg text-slate-200">상승 섹터 AI 분석</h2>
          <div className="flex items-center gap-1 ml-auto">
            <TrendingUp className="size-3 sm:size-4 text-green-400" />
            <span className="text-xs sm:text-sm text-green-400">상승 중</span>
          </div>
        </div>
        
        <div className="text-slate-300 leading-relaxed whitespace-pre-line text-sm">
          {risingSectorAnalysis}
        </div>

        <div className="mt-4 pt-4 border-t border-green-700/20">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>AI 분석 기준</span>
            <span>{updatedLabel}</span>
          </div>
        </div>
      </div>

      {/* Animation styles */}
      <style>{`
        @keyframes slide-up {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}