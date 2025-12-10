import { useState, useMemo, useEffect } from 'react';
import { Header } from './Header';
import { Search, X, Zap, ArrowLeft, TrendingUp, DollarSign, Brain, Shield, Sparkles, Check, Loader2 } from 'lucide-react';
import { analyzeMatchup, getRankings } from '../services/api';
import { MatchupResponse, RankingRead } from '../types';

interface Company {
  id: string;
  name: string;
  ticker: string;
  logoUrl: string;
  sector: string;
  rank: number;
}

export function ComparisonPage() {
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [matchup, setMatchup] = useState<MatchupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSector, setSelectedSector] = useState('전체');
  const [allCompanies, setAllCompanies] = useState<Company[]>([]);
  const [loadingCompanies, setLoadingCompanies] = useState(true);
  const [companiesError, setCompaniesError] = useState<string | null>(null);

  // Normalize sector name (map "기술/IT" to "기술", etc.)
  const normalizeSector = (sectorName: string | null): string => {
    if (!sectorName) return '기타';
    if (sectorName === '기술/IT') return '기술';
    return sectorName;
  };

  // Load companies from API (same as RankingListPage)
  useEffect(() => {
    let mounted = true;
    setLoadingCompanies(true);
    setCompaniesError(null);

    // Try 2025 first, fallback to 2024 if not available
    const loadRankings = async (year: number) => {
      try {
        const data: RankingRead[] = await getRankings(year, 100);
        if (!mounted) return;

        // Map API data to Company interface
        const mappedCompanies: Company[] = data.map((company) => ({
          id: `company-${company.ticker}`,
          name: company.name,
          ticker: company.ticker,
          logoUrl: company.logo_url || '',
          sector: normalizeSector(company.sector),
          rank: company.rank,
        }));

        setAllCompanies(mappedCompanies);
        setLoadingCompanies(false);
      } catch (err: any) {
        if (!mounted) return;
        
        // If 2025 fails, try 2024
        if (year === 2025) {
          loadRankings(2024);
        } else {
          setCompaniesError(err.message || 'Failed to load companies');
          setLoadingCompanies(false);
        }
      }
    };

    loadRankings(2025);

    return () => {
      mounted = false;
    };
  }, []);

  // Extract unique sectors from loaded companies
  const allSectors = useMemo(() => {
    const sectors = Array.from(new Set(allCompanies.map(c => c.sector))).sort();
    return ['전체', ...sectors];
  }, [allCompanies]);

  const handleSelectCompany = (company: Company) => {
    if (selectedCompanies.find(c => c.id === company.id)) {
      setSelectedCompanies(selectedCompanies.filter(c => c.id !== company.id));
    } else if (selectedCompanies.length < 2) {
      setSelectedCompanies([...selectedCompanies, company]);
    }
  };

  const handleAnalyze = async () => {
    if (selectedCompanies.length === 2) {
      setLoading(true);
      setError(null);
      try {
        const res = await analyzeMatchup([selectedCompanies[0].ticker, selectedCompanies[1].ticker]);
        setMatchup(res);
        setShowComparison(true);
      } catch (err) {
        setError((err as Error).message || '분석에 실패했습니다.');
      } finally {
        setLoading(false);
      }
    }
  };

  const handleBack = () => {
    setShowComparison(false);
    setSelectedCompanies([]);
    setMatchup(null);
  };

  const isSelected = (companyId: string) => {
    return selectedCompanies.some(c => c.id === companyId);
  };

  const clearSearch = () => {
    setSearchTerm('');
  };

  // Filter companies based on search term and selected sector
  const filteredCompanies = useMemo(() => {
    return allCompanies
      .filter(company => {
        if (selectedSector === '전체') return true;
        const normalizedSelected = normalizeSector(selectedSector);
        return company.sector === normalizedSelected;
      })
      .filter(company => 
        company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        company.ticker.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [searchTerm, selectedSector, allCompanies]);

  // State 2: Comparison Result View (Split-screen)
  if (showComparison && matchup && selectedCompanies.length === 2) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 pb-24">
        <Header />
        
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Back Button */}
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-slate-400 hover:text-blue-400 transition-colors mb-6"
          >
            <ArrowLeft className="size-5" />
            <span>새로운 비교</span>
          </button>

          {/* Split-view Header with VS */}
          <div className="mb-8">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-0">
                {/* Company 1 */}
                <div className="p-8 bg-gradient-to-br from-blue-500/10 to-transparent border-r border-slate-700">
                  <div className="flex flex-col items-center">
                    <div className="size-24 rounded-2xl bg-white flex items-center justify-center overflow-hidden ring-4 ring-blue-500 shadow-lg mb-4">
                      <img
                        src={selectedCompanies[0].logoUrl}
                        alt={selectedCompanies[0].name}
                        className="size-20 object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    </div>
                    <h2 className="text-xl text-slate-100 text-center mb-1">{selectedCompanies[0].name}</h2>
                    <div className="text-sm text-blue-400 mb-2">{selectedCompanies[0].ticker}</div>
                    <div className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-xs">
                      {selectedCompanies[0].sector}
                    </div>
                  </div>
                </div>

                {/* VS Section */}
                <div className="p-8 flex items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900">
                  <div className="relative">
                    <div className="size-24 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-2xl">
                      <span className="text-4xl text-white">VS</span>
                    </div>
                    <div className="absolute -inset-3 rounded-full bg-gradient-to-br from-blue-500/20 to-cyan-500/20 animate-pulse -z-10"></div>
                  </div>
                </div>

                {/* Company 2 */}
                <div className="p-8 bg-gradient-to-br from-cyan-500/10 to-transparent border-l border-slate-700">
                  <div className="flex flex-col items-center">
                    <div className="size-24 rounded-2xl bg-white flex items-center justify-center overflow-hidden ring-4 ring-cyan-500 shadow-lg mb-4">
                      <img
                        src={selectedCompanies[1].logoUrl}
                        alt={selectedCompanies[1].name}
                        className="size-20 object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    </div>
                    <h2 className="text-xl text-slate-100 text-center mb-1">{selectedCompanies[1].name}</h2>
                    <div className="text-sm text-cyan-400 mb-2">{selectedCompanies[1].ticker}</div>
                    <div className="px-3 py-1 bg-cyan-500/20 text-cyan-400 rounded-lg text-xs">
                      {selectedCompanies[1].sector}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Analysis Report Sections */}
          <div className="space-y-6">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-500/20 rounded-xl">
                  <DollarSign className="size-6 text-blue-400" />
                </div>
                <h3 className="text-2xl text-slate-100">AI 종합 요약</h3>
              </div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                {matchup.summary}
              </div>
            </div>

            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-500/20 rounded-xl">
                  <Brain className="size-6 text-purple-400" />
                </div>
                <h3 className="text-2xl text-slate-100">주요 비교 포인트</h3>
              </div>
              <div className="space-y-4">
                {matchup.key_comparison.map((item, idx) => (
                  <div key={idx} className="bg-slate-900/40 border border-slate-700/50 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-slate-200 font-semibold">{item.metric}</div>
                      <div className="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-300 text-sm">
                        승자: {item.winner}
                      </div>
                    </div>
                    <div className="text-slate-300 leading-relaxed">{item.reason}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/20 border border-blue-500/30 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-500/20 rounded-xl">
                  <Sparkles className="size-6 text-blue-400" />
                </div>
                <h3 className="text-2xl text-slate-100">AI 결정</h3>
              </div>
              <div className="flex flex-col gap-3">
                <div className="text-lg text-slate-200">
                  최종 승자: <span className="text-blue-300 font-semibold">{matchup.winner}</span>
                </div>
                <div className="text-slate-300 leading-relaxed bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                  {matchup.reason}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // State 1: Company Selection View
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-32">
      <Header />
      
      {/* Sticky Top Controls */}
      <div className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur-sm border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          {/* Page Title */}
          <div className="mb-4 text-center">
            <h1 className="text-3xl text-slate-100 mb-2">AI 기업 비교 분석</h1>
            <p className="text-sm text-slate-400">TOP 100 기업 중 2개를 선택하여 심층 비교</p>
          </div>

          {/* Search Bar */}
          <div className="mb-4">
            <div className="relative max-w-2xl mx-auto">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-5 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="티커 또는 기업명 검색"
                className="w-full pl-12 pr-12 py-4 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-lg"
              />
              {searchTerm && (
                <button
                  onClick={clearSearch}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <X className="size-5 text-slate-400" />
                </button>
              )}
            </div>
          </div>

          {/* Category Filter Chips */}
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
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading State */}
        {loadingCompanies && (
          <div className="flex flex-col items-center justify-center py-16">
            <Loader2 className="size-8 text-blue-500 animate-spin mb-4" />
            <div className="text-slate-400">기업 데이터를 불러오는 중...</div>
          </div>
        )}

        {/* Error State */}
        {companiesError && !loadingCompanies && (
          <div className="py-16 text-center">
            <div className="text-red-400 mb-2">오류가 발생했습니다</div>
            <div className="text-slate-400 text-sm">{companiesError}</div>
          </div>
        )}

        {/* Results Info */}
        {!loadingCompanies && !companiesError && (
          <div className="mb-4 text-sm text-slate-400">
            {filteredCompanies.length}개 기업 표시 중
          </div>
        )}

        {/* Company Grid */}
        {!loadingCompanies && !companiesError && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filteredCompanies.map((company) => {
            const selected = isSelected(company.id);
            const selectionIndex = selectedCompanies.findIndex(c => c.id === company.id);
            
            return (
              <button
                key={company.id}
                onClick={() => handleSelectCompany(company)}
                disabled={!selected && selectedCompanies.length >= 2}
                className={`relative p-5 rounded-xl border-2 transition-all duration-300 ${
                  selected
                    ? selectionIndex === 0
                      ? 'border-blue-500 bg-blue-500/10 ring-2 ring-blue-500/50 shadow-lg shadow-blue-500/20 scale-105'
                      : 'border-cyan-500 bg-cyan-500/10 ring-2 ring-cyan-500/50 shadow-lg shadow-cyan-500/20 scale-105'
                    : 'border-slate-700 bg-slate-900/50 hover:border-slate-600 hover:bg-slate-900 hover:scale-102'
                } ${!selected && selectedCompanies.length >= 2 ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                {/* Rank Badge */}
                <div className="absolute top-2 left-2 px-2 py-1 bg-slate-800 rounded-md text-xs text-slate-400">
                  #{company.rank}
                </div>

                {/* Selection Badge */}
                {selected && (
                  <div className={`absolute -top-2 -right-2 size-8 rounded-full flex items-center justify-center ${
                    selectionIndex === 0 ? 'bg-blue-500' : 'bg-cyan-500'
                  } shadow-lg z-10 ring-2 ring-slate-950`}>
                    <Check className="size-5 text-white" />
                  </div>
                )}

                {/* Company Logo */}
                <div className="size-20 mx-auto mb-3 rounded-xl bg-white flex items-center justify-center overflow-hidden relative">
                  {company.logoUrl ? (
                    <>
                      <img
                        src={company.logoUrl}
                        alt={company.name}
                        className="size-16 object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const fallback = e.currentTarget.parentElement?.querySelector('.logo-fallback') as HTMLElement;
                          if (fallback) fallback.style.display = 'flex';
                        }}
                      />
                      <div className="logo-fallback hidden absolute inset-0 items-center justify-center">
                        <span className="text-xs font-semibold text-slate-700 text-center px-1">
                          {company.ticker}
                        </span>
                      </div>
                    </>
                  ) : (
                    <span className="text-xs font-semibold text-slate-700 text-center px-1">
                      {company.ticker}
                    </span>
                  )}
                </div>

                {/* Company Info */}
                <div className="text-center">
                  <div className="text-sm text-slate-200 mb-1 line-clamp-2 min-h-[2.5rem]">{company.name}</div>
                  <div className="px-2 py-1 bg-slate-800 rounded text-xs text-blue-400 mb-2 inline-block">
                    {company.ticker}
                  </div>
                  <div className="text-xs text-slate-500">{company.sector}</div>
                </div>
              </button>
            );
          })}
          </div>
        )}

        {/* Empty State */}
        {!loadingCompanies && !companiesError && filteredCompanies.length === 0 && (
          <div className="text-center py-16">
            <p className="text-slate-400 mb-4">검색 결과가 없습니다</p>
            <button
              onClick={() => {
                setSearchTerm('');
                setSelectedSector('전체');
              }}
              className="text-blue-400 hover:text-blue-300 transition-colors"
            >
              필터 초기화
            </button>
          </div>
        )}
      </main>

      {/* Fixed Bottom Action Button */}
      <div className="fixed bottom-20 left-0 right-0 z-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={handleAnalyze}
            disabled={selectedCompanies.length !== 2 || loading}
            className={`w-full max-w-md mx-auto flex items-center justify-center gap-3 px-8 py-5 rounded-2xl shadow-2xl transition-all duration-300 ${
              selectedCompanies.length === 2 && !loading
                ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-blue-500/50 hover:scale-105 cursor-pointer'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-slate-300 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Zap className={`size-6 ${selectedCompanies.length === 2 ? 'animate-pulse' : ''}`} />
            )}
            <span className="text-xl">
              비교하기 ({selectedCompanies.length}/2)
            </span>
          </button>
          {error && (
            <div className="mt-2 text-sm text-red-400 text-center">{error}</div>
          )}
        </div>
      </div>
    </div>
  );
}