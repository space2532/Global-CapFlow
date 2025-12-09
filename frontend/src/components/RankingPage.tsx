import { useEffect, useMemo, useState } from 'react';
import { Award, TrendingDown, TrendingUp } from 'lucide-react';
import { Header } from './Header';
import { getRankings } from '../services/api';
import { RankingRead } from '../types';

interface RankingPageProps {
  onViewProfile?: (ticker: string) => void;
}

function getRankBadgeColor(rank: number): string {
  if (rank === 1) return 'bg-gradient-to-br from-yellow-400 to-amber-500 text-white';
  if (rank === 2) return 'bg-gradient-to-br from-slate-300 to-slate-400 text-slate-900';
  if (rank === 3) return 'bg-gradient-to-br from-amber-600 to-amber-700 text-white';
  return 'bg-slate-700 text-slate-300';
}

function formatMarketCap(value: number | null) {
  if (!value) return 'N/A';
  const trillion = 1_000_000_000_000;
  const billion = 1_000_000_000;

  if (value >= trillion) {
    return `$${(value / trillion).toFixed(1)}T`;
  }
  if (value >= billion) {
    return `$${(value / billion).toFixed(1)}B`;
  }
  return `$${value.toLocaleString()}`;
}

export function RankingPage({ onViewProfile }: RankingPageProps) {
  const [selectedYear, setSelectedYear] = useState(2025);
  const [rankings, setRankings] = useState<RankingRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    getRankings(selectedYear, 20)
      .then((data) => {
        if (mounted) setRankings(data);
      })
      .catch((err) => {
        if (mounted) setError(err.message || 'Failed to load rankings');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [selectedYear]);

  const maxMarketCap = useMemo(() => {
    if (!rankings.length) return 0;
    return Math.max(...rankings.map((c) => c.market_cap ?? 0));
  }, [rankings]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-24">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Award className="size-8 text-blue-400" />
            <h1 className="text-3xl text-slate-100">글로벌 TOP 20 기업</h1>
          </div>
          <p className="text-slate-400">시가총액 기준 순위</p>
        </div>

        {/* Year Filter - Horizontal Scrollable Button Group */}
        <div className="mb-8">
          <div className="relative">
            <div className="overflow-x-auto scrollbar-hide">
              <div className="flex gap-3 pb-2">
                {years.map((year) => (
                  <button
                    key={year}
                    onClick={() => setSelectedYear(year)}
                    className={`px-6 py-3 rounded-xl whitespace-nowrap transition-all flex-shrink-0 ${
                      selectedYear === year
                        ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30 scale-105'
                        : 'bg-slate-800/50 text-slate-300 hover:bg-slate-800 border border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    <span>{year}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Gradient fade edges for scroll indication */}
            <div className="absolute top-0 right-0 h-full w-12 bg-gradient-to-l from-slate-950 to-transparent pointer-events-none"></div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chart Section */}
          <div className="lg:col-span-2">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl min-h-[320px] flex items-center justify-center">
              {loading ? (
                <div className="flex items-center gap-3 text-slate-300">
                  <div className="w-5 h-5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
                  <span>불러오는 중...</span>
                </div>
              ) : error ? (
                <div className="text-red-400">{error}</div>
              ) : rankings.length === 0 ? (
                <div className="text-slate-400">데이터가 없습니다.</div>
              ) : (
                <div className="w-full space-y-3">
                  {rankings.map((company) => {
                    const barWidth =
                      maxMarketCap && company.market_cap
                        ? (company.market_cap / maxMarketCap) * 100
                        : 0;

                    return (
                      <button
                        key={`${company.year}-${company.rank}-${company.ticker}`}
                        className="w-full text-left group"
                        onClick={() => onViewProfile && company.ticker && onViewProfile(company.ticker)}
                      >
                        <div className="relative bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-blue-500/50 rounded-xl p-4 transition-all duration-300 cursor-pointer">
                          {/* Background bar */}
                          <div
                            className="absolute left-0 top-0 h-full bg-gradient-to-r from-blue-500/20 to-cyan-500/10 rounded-xl transition-all duration-500 group-hover:from-blue-500/30 group-hover:to-cyan-500/20"
                            style={{ width: `${barWidth}%` }}
                          ></div>

                          {/* Content */}
                          <div className="relative flex items-center gap-4">
                            {/* Rank Badge */}
                            <div className={`${getRankBadgeColor(company.rank)} w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg`}>
                              <span className="text-lg">{company.rank}</span>
                            </div>

                            {/* Company Logo Placeholder */}
                            <div className="size-12 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0 text-slate-200 ring-2 ring-slate-700 group-hover:ring-blue-500 transition-all">
                              <span className="text-sm font-semibold">{company.ticker}</span>
                            </div>

                            {/* Company Info */}
                            <div className="flex-1 min-w-0">
                              <div className="text-slate-200 group-hover:text-blue-400 transition-colors">
                                {company.name}
                              </div>
                              <div className="text-sm text-slate-400">
                                {company.sector || company.industry || 'N/A'}
                              </div>
                            </div>

                            {/* Market Cap */}
                            <div className="text-right flex-shrink-0">
                              <div className="text-lg text-slate-200">
                                {formatMarketCap(company.market_cap ?? null)}
                              </div>
                              <div className="text-xs text-slate-500">시가총액</div>
                            </div>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Movers Panel (placeholder / could be enhanced with API later) */}
          <div className="lg:col-span-1">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl sticky top-24">
              <h2 className="text-lg text-slate-200 mb-6">신규 진입 & 이탈</h2>
              <div className="text-slate-500 text-sm">추후 데이터 연동 예정</div>
              <div className="mt-4 flex items-center gap-2 text-slate-400">
                <TrendingUp className="size-5" /> <span>상위 변동 추적 준비중</span>
              </div>
              <div className="mt-2 flex items-center gap-2 text-slate-400">
                <TrendingDown className="size-5" /> <span>이탈 기업 데이터 준비중</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}