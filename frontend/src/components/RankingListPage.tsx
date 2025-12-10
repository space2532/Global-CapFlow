import React from 'react';
import { useState, useMemo, useEffect } from 'react';
import { Header } from './Header';
import { Search, Filter, TrendingUp, TrendingDown, Minus, Award, ChevronDown, Loader2 } from 'lucide-react';
import { getRankings } from '../services/api';
import { RankingRead } from '../types';

// Company Logo Component with fallback
function CompanyLogo({ logoUrl, ticker, name, size = 'md' }: { logoUrl: string | null; ticker: string; name: string; size?: 'sm' | 'md' }) {
  const containerSize = size === 'sm' ? 'size-8' : 'size-10';
  const imageSize = size === 'sm' ? 'size-6' : 'size-8';
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <div className={`${containerSize} rounded-full bg-white flex items-center justify-center flex-shrink-0 overflow-hidden`}>
      {logoUrl ? (
        <img
          src={logoUrl}
          alt={name}
          className={`${imageSize} object-contain`}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
          }}
        />
      ) : (
        <span className={`${textSize} font-semibold text-slate-700`}>{ticker}</span>
      )}
    </div>
  );
}

interface RankingCompany {
  rank: number;
  name: string;
  ticker: string;
  logoUrl: string | null;
  marketCap: string;
  marketCapValue: number;
  sector: string;
  industry: string;
  country: string;
  rankChange: number; // positive = up, negative = down, 0 = no change
  isNewEntry: boolean;
}

interface RankingListPageProps {
  onViewProfile?: (ticker: string) => void;
  sector?: string;
}

function formatMarketCap(value: number | null): string {
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

function getRankChangeIcon(change: number) {
  if (change === 999) return { icon: Award, color: 'text-green-400', label: 'NEW' };
  if (change > 0) return { icon: TrendingUp, color: 'text-green-400', label: `+${change}` };
  if (change < 0) return { icon: TrendingDown, color: 'text-red-400', label: `${change}` };
  return { icon: Minus, color: 'text-slate-500', label: '—' };
}

export function RankingListPage({ onViewProfile, sector }: RankingListPageProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>(sector || '전체');
  const [companies, setCompanies] = useState<RankingCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Normalize sector name (map "기술/IT" to "기술", etc.)
  const normalizeSector = (sectorName: string): string => {
    if (sectorName === '기술/IT') return '기술';
    return sectorName;
  };

  // Load rankings data from API
  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    // Try 2025 first, fallback to 2024 if not available
    const loadRankings = async (year: number) => {
      try {
        const data: RankingRead[] = await getRankings(year, 100);
        if (!mounted) return;

        // Map API data to RankingCompany interface
        const mappedCompanies: RankingCompany[] = data.map((company) => ({
          rank: company.rank,
          name: company.name,
          ticker: company.ticker,
          logoUrl: company.logo_url || '',
          marketCap: formatMarketCap(company.market_cap),
          marketCapValue: company.market_cap || 0,
          sector: company.sector || '기타',
          industry: company.industry || 'N/A',
          country: company.country || 'N/A',
          rankChange: 0, // 임시
          isNewEntry: false, // 임시
        }));

        setCompanies(mappedCompanies);
        setLoading(false);
      } catch (err: any) {
        if (!mounted) return;
        
        // If 2025 fails, try 2024
        if (year === 2025) {
          loadRankings(2024);
        } else {
          setError(err.message || 'Failed to load rankings');
          setLoading(false);
        }
      }
    };

    loadRankings(2025);

    return () => {
      mounted = false;
    };
  }, []);

  // Get unique sectors from loaded companies
  const allSectors = useMemo(() => {
    const sectors = Array.from(new Set(companies.map(c => c.sector))).sort();
    return ['전체', ...sectors];
  }, [companies]);

  const filteredCompanies = useMemo(() => {
    return companies.filter(company => {
      const matchesSearch = searchQuery === '' ||
        company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        company.ticker.toLowerCase().includes(searchQuery.toLowerCase());
      
      const normalizedSelected = normalizeSector(selectedSector);
      const matchesSector = selectedSector === '전체' || company.sector === normalizedSelected;
      
      return matchesSearch && matchesSector;
    });
  }, [searchQuery, selectedSector, companies]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-24">
      <Header />
      
      {/* Sticky Top Controls */}
      <div className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          {/* Page Header */}
          <div className="mb-4">
            <h1 className="text-3xl text-slate-100 mb-1">글로벌 TOP 100 기업 순위</h1>
            <p className="text-sm text-slate-400">시가총액 기준 전체 순위 및 변동 추이</p>
          </div>

          {/* Search Bar */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-5 text-slate-400" />
              <input
                type="text"
                placeholder="티커 또는 기업명 검색"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-lg"
              />
            </div>
          </div>

          {/* Category Filters (Horizontal Scroll) */}
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
            {allSectors.map((sector) => (
              <button
                key={sector}
                onClick={() => setSelectedSector(sector)}
                className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all flex-shrink-0 ${
                  selectedSector === sector
                    ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                }`}
              >
                {sector}
              </button>
            ))}
          </div>

          {/* Results Count */}
          {(searchQuery || selectedSector !== '전체') && (
            <div className="mt-3 flex items-center gap-2 text-sm text-slate-400">
              <span>{filteredCompanies.length}개 기업 표시 중</span>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedSector('전체');
                }}
                className="text-blue-400 hover:text-blue-300 transition-colors"
              >
                • 초기화
              </button>
            </div>
          )}
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16">
            <Loader2 className="size-8 text-blue-500 animate-spin mb-4" />
            <div className="text-slate-400">데이터를 불러오는 중...</div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="py-16 text-center">
            <div className="text-red-400 mb-2">오류가 발생했습니다</div>
            <div className="text-slate-400 text-sm">{error}</div>
          </div>
        )}

        {/* Data Table - Desktop */}
        {!loading && !error && (
          <div className="hidden md:block bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl shadow-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-800/70 border-b border-slate-700">
                  <th className="px-6 py-4 text-left text-sm text-slate-300 w-24">순위</th>
                  <th className="px-6 py-4 text-left text-sm text-slate-300">기업</th>
                  <th className="px-6 py-4 text-right text-sm text-slate-300">시가총액</th>
                  <th className="px-6 py-4 text-left text-sm text-slate-300">섹터</th>
                  <th className="px-6 py-4 text-left text-sm text-slate-300">산업</th>
                  <th className="px-6 py-4 text-center text-sm text-slate-300">국가</th>
                  <th className="px-6 py-4 text-center text-sm text-slate-300">변동</th>
                </tr>
              </thead>
              <tbody>
                {filteredCompanies.map((company, index) => {
                  const rankChange = getRankChangeIcon(company.rankChange);
                  const RankIcon = rankChange.icon;
                  
                  return (
                    <tr
                      key={company.ticker}
                      onClick={() => onViewProfile && onViewProfile(company.ticker)}
                      className={`border-b border-slate-800 hover:bg-slate-800/50 transition-colors cursor-pointer ${
                        company.isNewEntry ? 'bg-green-500/5' : index % 2 === 0 ? 'bg-slate-900/20' : 'bg-slate-900/40'
                      }`}
                    >
                      {/* Rank */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-lg text-slate-200">{company.rank}</span>
                        </div>
                      </td>

                      {/* Company */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <CompanyLogo logoUrl={company.logoUrl} ticker={company.ticker} name={company.name} size="md" />
                          <div className="min-w-0">
                            <div className="text-slate-200 hover:text-blue-400 transition-colors">
                              {company.name}
                            </div>
                            <div className="text-sm text-slate-500">{company.ticker}</div>
                          </div>
                          {company.isNewEntry && (
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-md flex-shrink-0">
                              NEW
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Market Cap */}
                      <td className="px-6 py-4 text-right text-slate-200">
                        {company.marketCap}
                      </td>

                      {/* Sector */}
                      <td className="px-6 py-4">
                        <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm">
                          {company.sector}
                        </span>
                      </td>

                      {/* Industry */}
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {company.industry}
                      </td>

                      {/* Country */}
                      <td className="px-6 py-4 text-center">
                        <span className="text-sm text-slate-400" title={company.country}>{company.country}</span>
                      </td>

                      {/* Rank Change */}
                      <td className="px-6 py-4">
                        <div className={`flex items-center justify-center gap-1 ${rankChange.color}`}>
                          <RankIcon className="size-4" />
                          <span className="text-sm">{rankChange.label}</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
        )}

        {/* Mobile Card List */}
        {!loading && !error && (
          <div className="md:hidden space-y-3">
          {filteredCompanies.map((company, index) => {
            const rankChange = getRankChangeIcon(company.rankChange);
            const RankIcon = rankChange.icon;
            
            return (
              <div
                key={company.ticker}
                onClick={() => onViewProfile && onViewProfile(company.ticker)}
                className={`bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-xl p-4 shadow-lg active:scale-98 transition-all ${
                  company.isNewEntry ? 'ring-1 ring-green-500/30' : ''
                }`}
              >
                {/* Top Row: Rank, Company Info, Change */}
                <div className="flex items-start gap-3 mb-3">
                  {/* Rank Badge */}
                  <div className="flex-shrink-0 size-12 rounded-xl bg-slate-800/50 flex items-center justify-center">
                    <span className="text-lg text-slate-200">{company.rank}</span>
                  </div>

                  {/* Company Logo & Name */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <CompanyLogo logoUrl={company.logoUrl} ticker={company.ticker} name={company.name} size="sm" />
                      <div className="min-w-0">
                        <div className="text-slate-200 line-clamp-1">{company.name}</div>
                      </div>
                    </div>
                    <div className="text-xs text-slate-500">{company.ticker}</div>
                  </div>

                  {/* Rank Change */}
                  <div className={`flex-shrink-0 flex items-center gap-1 ${rankChange.color}`}>
                    <RankIcon className="size-4" />
                    <span className="text-sm">{rankChange.label}</span>
                  </div>
                </div>

                {/* Bottom Row: Details Grid */}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-700/50">
                  {/* Market Cap */}
                  <div>
                    <div className="text-xs text-slate-500 mb-1">시가총액</div>
                    <div className="text-slate-200">{company.marketCap}</div>
                  </div>

                  {/* Sector */}
                  <div>
                    <div className="text-xs text-slate-500 mb-1">섹터</div>
                    <span className="inline-block px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                      {company.sector}
                    </span>
                  </div>

                  {/* Industry */}
                  <div>
                    <div className="text-xs text-slate-500 mb-1">산업</div>
                    <div className="text-sm text-slate-400 line-clamp-1">{company.industry}</div>
                  </div>

                  {/* Country */}
                  <div>
                    <div className="text-xs text-slate-500 mb-1">국가</div>
                    <div className="flex items-center gap-1 text-sm text-slate-400">
                      <span className="font-semibold text-slate-200">{company.country}</span>
                    </div>
                  </div>
                </div>

                {/* NEW Badge */}
                {company.isNewEntry && (
                  <div className="mt-3 pt-3 border-t border-slate-700/50">
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-md">
                      <Award className="size-3" />
                      신규 진입
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        )}

        {/* Empty State */}
        {!loading && !error && filteredCompanies.length === 0 && (
          <div className="py-16 text-center">
            <div className="text-slate-400 mb-2">검색 결과가 없습니다</div>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedSector('전체');
              }}
              className="text-blue-400 hover:text-blue-300 transition-colors"
            >
              필터 초기화
            </button>
          </div>
        )}
      </main>
    </div>
  );
}