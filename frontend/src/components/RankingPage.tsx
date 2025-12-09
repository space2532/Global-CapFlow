import { Header } from './Header';
import { TrendingUp, TrendingDown, Award } from 'lucide-react';
import { useState } from 'react';

interface Company {
  rank: number;
  name: string;
  logoUrl: string;
  marketCap: string;
  marketCapValue: number;
  sector: string;
  ticker?: string;
}

interface Mover {
  name: string;
  ticker: string;
  logoUrl: string;
  previousRank?: number;
}

interface RankingPageProps {
  onViewProfile?: (ticker: string) => void;
}

const companies: Company[] = [
  { rank: 1, name: 'Apple Inc.', ticker: 'AAPL', logoUrl: 'https://logo.clearbit.com/apple.com', marketCap: '$3.2T', marketCapValue: 3200, sector: '기술' },
  { rank: 2, name: 'Microsoft Corp.', ticker: 'MSFT', logoUrl: 'https://logo.clearbit.com/microsoft.com', marketCap: '$2.9T', marketCapValue: 2900, sector: '기술' },
  { rank: 3, name: 'Saudi Aramco', ticker: 'ARAMCO', logoUrl: 'https://logo.clearbit.com/aramco.com', marketCap: '$2.1T', marketCapValue: 2100, sector: '에너지' },
  { rank: 4, name: 'Alphabet Inc.', ticker: 'GOOGL', logoUrl: 'https://logo.clearbit.com/google.com', marketCap: '$1.8T', marketCapValue: 1800, sector: '기술' },
  { rank: 5, name: 'Amazon.com', ticker: 'AMZN', logoUrl: 'https://logo.clearbit.com/amazon.com', marketCap: '$1.6T', marketCapValue: 1600, sector: '소비재' },
  { rank: 6, name: 'NVIDIA Corp.', ticker: 'NVDA', logoUrl: 'https://logo.clearbit.com/nvidia.com', marketCap: '$1.5T', marketCapValue: 1500, sector: '반도체' },
  { rank: 7, name: 'Tesla Inc.', ticker: 'TSLA', logoUrl: 'https://logo.clearbit.com/tesla.com', marketCap: '$1.2T', marketCapValue: 1200, sector: '자동차' },
  { rank: 8, name: 'Meta Platforms', ticker: 'META', logoUrl: 'https://logo.clearbit.com/meta.com', marketCap: '$1.1T', marketCapValue: 1100, sector: '기술' },
  { rank: 9, name: 'Berkshire Hathaway', ticker: 'BRK.B', logoUrl: 'https://logo.clearbit.com/berkshirehathaway.com', marketCap: '$890B', marketCapValue: 890, sector: '금융' },
  { rank: 10, name: 'TSMC', ticker: 'TSM', logoUrl: 'https://logo.clearbit.com/tsmc.com', marketCap: '$850B', marketCapValue: 850, sector: '반도체' },
  { rank: 11, name: 'Visa Inc.', ticker: 'V', logoUrl: 'https://logo.clearbit.com/visa.com', marketCap: '$610B', marketCapValue: 610, sector: '금융' },
  { rank: 12, name: 'JPMorgan Chase', ticker: 'JPM', logoUrl: 'https://logo.clearbit.com/jpmorganchase.com', marketCap: '$580B', marketCapValue: 580, sector: '금융' },
  { rank: 13, name: 'Samsung Electronics', ticker: '005930.KS', logoUrl: 'https://logo.clearbit.com/samsung.com', marketCap: '$520B', marketCapValue: 520, sector: '기술' },
  { rank: 14, name: 'Johnson & Johnson', ticker: 'JNJ', logoUrl: 'https://logo.clearbit.com/jnj.com', marketCap: '$480B', marketCapValue: 480, sector: '헬스케어' },
  { rank: 15, name: 'UnitedHealth Group', ticker: 'UNH', logoUrl: 'https://logo.clearbit.com/unitedhealthgroup.com', marketCap: '$470B', marketCapValue: 470, sector: '헬스케어' },
  { rank: 16, name: 'Walmart Inc.', ticker: 'WMT', logoUrl: 'https://logo.clearbit.com/walmart.com', marketCap: '$450B', marketCapValue: 450, sector: '소비재' },
  { rank: 17, name: 'Mastercard Inc.', ticker: 'MA', logoUrl: 'https://logo.clearbit.com/mastercard.com', marketCap: '$420B', marketCapValue: 420, sector: '금융' },
  { rank: 18, name: 'Exxon Mobil', ticker: 'XOM', logoUrl: 'https://logo.clearbit.com/exxonmobil.com', marketCap: '$410B', marketCapValue: 410, sector: '에너지' },
  { rank: 19, name: 'Procter & Gamble', ticker: 'PG', logoUrl: 'https://logo.clearbit.com/pg.com', marketCap: '$390B', marketCapValue: 390, sector: '소비재' },
  { rank: 20, name: 'LVMH', ticker: 'MC.PA', logoUrl: 'https://logo.clearbit.com/lvmh.com', marketCap: '$380B', marketCapValue: 380, sector: '소비재' },
];

const newEntries: Mover[] = [
  { name: 'NVIDIA Corp.', ticker: 'NVDA', logoUrl: 'https://logo.clearbit.com/nvidia.com', previousRank: 12 },
  { name: 'Tesla Inc.', ticker: 'TSLA', logoUrl: 'https://logo.clearbit.com/tesla.com', previousRank: 25 },
  { name: 'TSMC', ticker: 'TSM', logoUrl: 'https://logo.clearbit.com/tsmc.com', previousRank: 22 },
];

const exits: Mover[] = [
  { name: 'Tencent Holdings', ticker: 'TCEHY', logoUrl: 'https://logo.clearbit.com/tencent.com' },
  { name: 'Bank of America', ticker: 'BAC', logoUrl: 'https://logo.clearbit.com/bankofamerica.com' },
];

const maxMarketCap = Math.max(...companies.map(c => c.marketCapValue));

function getRankBadgeColor(rank: number): string {
  if (rank === 1) return 'bg-gradient-to-br from-yellow-400 to-amber-500 text-white';
  if (rank === 2) return 'bg-gradient-to-br from-slate-300 to-slate-400 text-slate-900';
  if (rank === 3) return 'bg-gradient-to-br from-amber-600 to-amber-700 text-white';
  return 'bg-slate-700 text-slate-300';
}

export function RankingPage({ onViewProfile }: RankingPageProps) {
  const [selectedYear, setSelectedYear] = useState(2025);
  const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
  
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
                    <span className={selectedYear === year ? '' : ''}>{year}</span>
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
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="space-y-3">
                {companies.map((company) => {
                  const barWidth = (company.marketCapValue / maxMarketCap) * 100;
                  
                  return (
                    <button
                      key={company.rank}
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
                          <div className="size-12 rounded-full bg-white flex items-center justify-center flex-shrink-0 overflow-hidden ring-2 ring-slate-700 group-hover:ring-blue-500 transition-all">
                            <img
                              src={company.logoUrl}
                              alt={company.name}
                              className="size-10 object-contain"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          </div>
                          
                          {/* Company Info */}
                          <div className="flex-1 min-w-0">
                            <div className="text-slate-200 group-hover:text-blue-400 transition-colors">
                              {company.name}
                            </div>
                            <div className="text-sm text-slate-400">{company.sector}</div>
                          </div>
                          
                          {/* Market Cap */}
                          <div className="text-right flex-shrink-0">
                            <div className="text-lg text-slate-200">{company.marketCap}</div>
                            <div className="text-xs text-slate-500">시가총액</div>
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Movers Panel */}
          <div className="lg:col-span-1">
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl sticky top-24">
              <h2 className="text-lg text-slate-200 mb-6">신규 진입 & 이탈</h2>
              
              {/* New Entries */}
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="size-5 text-green-400" />
                  <h3 className="text-slate-300">신규 진입</h3>
                </div>
                <div className="space-y-3">
                  {newEntries.map((mover, index) => (
                    <div
                      key={index}
                      className="bg-green-500/10 border border-green-500/30 rounded-xl p-3 hover:bg-green-500/20 transition-colors cursor-pointer"
                      onClick={() => onViewProfile && onViewProfile(mover.ticker)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="size-10 rounded-full bg-white flex items-center justify-center flex-shrink-0 overflow-hidden">
                          <img
                            src={mover.logoUrl}
                            alt={mover.name}
                            className="size-8 object-contain"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-slate-200 truncate">{mover.name}</div>
                          {mover.previousRank && (
                            <div className="text-xs text-green-400">
                              #{mover.previousRank} → TOP 20
                            </div>
                          )}
                        </div>
                        <TrendingUp className="size-4 text-green-400 flex-shrink-0" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Exits */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <TrendingDown className="size-5 text-red-400" />
                  <h3 className="text-slate-300">순위 이탈</h3>
                </div>
                <div className="space-y-3">
                  {exits.map((mover, index) => (
                    <div
                      key={index}
                      className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 hover:bg-red-500/20 transition-colors cursor-pointer"
                      onClick={() => onViewProfile && onViewProfile(mover.ticker)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="size-10 rounded-full bg-white flex items-center justify-center flex-shrink-0 overflow-hidden">
                          <img
                            src={mover.logoUrl}
                            alt={mover.name}
                            className="size-8 object-contain"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-slate-200 truncate">{mover.name}</div>
                          <div className="text-xs text-red-400">TOP 20 이탈</div>
                        </div>
                        <TrendingDown className="size-4 text-red-400 flex-shrink-0" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Stats Footer */}
              <div className="mt-6 pt-4 border-t border-slate-700">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl text-green-400">{newEntries.length}</div>
                    <div className="text-xs text-slate-400">신규 진입</div>
                  </div>
                  <div>
                    <div className="text-2xl text-red-400">{exits.length}</div>
                    <div className="text-xs text-slate-400">순위 이탈</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}