import React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { Award, TrendingDown, TrendingUp, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { Header } from './Header';
import { getRankingMovers, getRankings } from '../services/api';
import { RankingMovers, RankingRead } from '../types';

// Company Logo Component with fallback
function CompanyLogo({ logoUrl, ticker, name }: { logoUrl: string | null; ticker: string; name: string }) {
  const [showFallback, setShowFallback] = useState(false);

  return (
    <div className="size-12 rounded-full bg-white flex items-center justify-center flex-shrink-0 overflow-hidden ring-2 ring-slate-700 group-hover:ring-blue-500 transition-all">
      {!showFallback && logoUrl ? (
        <img
          src={logoUrl}
          alt={name}
          className="size-12 rounded-full object-contain"
          onError={() => setShowFallback(true)}
        />
      ) : (
        <span className="text-sm font-semibold text-slate-700">{ticker}</span>
      )}
    </div>
  );
}

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
  const [movers, setMovers] = useState<RankingMovers | null>(null);
  const [loading, setLoading] = useState(false);
  const [moversLoading, setMoversLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moversError, setMoversError] = useState<string | null>(null);

  const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
  const TOP_LIMIT = 20;
  const filteredNewEntries = useMemo(
    () =>
      movers?.new_entries.filter((item) => item.rank !== null && item.rank <= TOP_LIMIT) || [],
    [movers]
  );

  const filteredExited = useMemo(
    () =>
      movers?.exited.filter((item) => item.rank !== null && item.rank <= TOP_LIMIT) || [],
    [movers]
  );


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

  useEffect(() => {
    let mounted = true;
    setMoversLoading(true);
    setMoversError(null);

    getRankingMovers()
      .then((data) => {
        if (!mounted) return;
        setMovers(data);
      })
      .catch((err) => {
        if (!mounted) return;
        setMoversError(err.message || '신규 진입/이탈 데이터를 불러오지 못했습니다.');
      })
      .finally(() => {
        if (mounted) setMoversLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

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

                            {/* Company Logo */}
                            <CompanyLogo logoUrl={company.logo_url} ticker={company.ticker} name={company.name} />

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

          {/* Movers Panel */}
          <div className="lg:col-span-1 self-start">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl sticky top-20">
              <h2 className="text-lg text-slate-200 mb-6">신규 진입 & 이탈</h2>
              {moversLoading ? (
                <div className="text-slate-500 text-sm">불러오는 중...</div>
              ) : moversError ? (
                <div className="text-red-400 text-sm">{moversError}</div>
              ) : movers && (filteredNewEntries.length > 0 || filteredExited.length > 0) ? (
                <div className="space-y-6">
                  <div>
                    <div className="flex items-center gap-2 text-green-300 mb-2">
                      <TrendingUp className="size-5" />
                      <span className="font-semibold">신규 진입</span>
                    </div>
                    {filteredNewEntries.length === 0 ? (
                      <div className="text-slate-500 text-sm">Top 20 신규 진입 없음</div>
                    ) : (
                      <ul className="space-y-3">
                        {filteredNewEntries.map((item) => (
                          <li key={item.ticker} className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-3">
                              <div className="size-10 rounded-full bg-white flex items-center justify-center overflow-hidden ring-2 ring-slate-700">
                                {item.logo_url ? (
                                  <img src={item.logo_url} alt={item.name} className="size-10 object-contain" />
                                ) : (
                                  <span className="text-xs font-semibold text-slate-700">{item.ticker}</span>
                                )}
                              </div>
                              <div>
                                <div className="text-slate-100 text-sm font-semibold">{item.name}</div>
                                <div className="text-xs text-slate-500">{item.ticker}</div>
                              </div>
                            </div>
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/20 text-green-300 text-xs rounded">
                              <ArrowUpRight className="size-4" />
                              {item.rank ? `#${item.rank}` : 'Top 100'}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div>
                    <div className="flex items-center gap-2 text-amber-300 mb-2">
                      <TrendingDown className="size-5" />
                      <span className="font-semibold">이탈</span>
                    </div>
                    {filteredExited.length === 0 ? (
                      <div className="text-slate-500 text-sm">Top 20 이탈 없음</div>
                    ) : (
                      <ul className="space-y-3">
                        {filteredExited.map((item) => (
                          <li key={item.ticker} className="flex items-center justify-between gap-3">
                            <div className="flex items-center gap-3">
                              <div className="size-10 rounded-full bg-white flex items-center justify-center overflow-hidden ring-2 ring-slate-700">
                                {item.logo_url ? (
                                  <img src={item.logo_url} alt={item.name} className="size-10 object-contain" />
                                ) : (
                                  <span className="text-xs font-semibold text-slate-700">{item.ticker}</span>
                                )}
                              </div>
                              <div>
                                <div className="text-slate-100 text-sm font-semibold">{item.name}</div>
                                <div className="text-xs text-slate-500">{item.ticker}</div>
                              </div>
                            </div>
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-500/20 text-amber-300 text-xs rounded">
                              <ArrowDownRight className="size-4" />
                              이탈
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-slate-500 text-sm">표시할 데이터가 없습니다.</div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}