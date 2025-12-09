import { TrendingUp, TrendingDown, Award, XCircle } from 'lucide-react';

interface RankingCompany {
  name: string;
  ticker: string;
  logoUrl: string;
  rank?: number;
  previousRank?: number;
}

interface RankingWidgetProps {
  onViewProfile?: (ticker: string) => void;
}

// Companies entering Top 100 (New Entry)
const newEntries: RankingCompany[] = [
  { name: 'Palantir Technologies', ticker: 'PLTR', logoUrl: 'https://logo.clearbit.com/palantir.com', rank: 87 },
  { name: 'Snowflake Inc.', ticker: 'SNOW', logoUrl: 'https://logo.clearbit.com/snowflake.com', rank: 92 },
  { name: 'Rivian Automotive', ticker: 'RIVN', logoUrl: 'https://logo.clearbit.com/rivian.com', rank: 95 },
  { name: 'Block Inc.', ticker: 'SQ', logoUrl: 'https://logo.clearbit.com/block.xyz', rank: 98 },
];

// Companies dropping out of Top 100
const droppedOut: RankingCompany[] = [
  { name: 'Twitter/X Corp.', ticker: 'X', logoUrl: 'https://logo.clearbit.com/twitter.com', previousRank: 94 },
  { name: 'Zoom Video', ticker: 'ZM', logoUrl: 'https://logo.clearbit.com/zoom.us', previousRank: 89 },
  { name: 'Peloton Interactive', ticker: 'PTON', logoUrl: 'https://logo.clearbit.com/onepeloton.com', previousRank: 96 },
];

export function RankingWidget({ onViewProfile }: RankingWidgetProps) {
  return (
    <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl h-full flex flex-col">
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-purple-500/20 p-2 rounded-lg">
          <Award className="size-5 text-purple-400" />
        </div>
        <h2 className="text-lg text-slate-200">순위 변동: 진입 & 이탈</h2>
      </div>
      
      <div className="flex-1 space-y-6">
        {/* Section A: New Entries (Green) */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
              <TrendingUp className="size-4 text-green-400" />
              <span className="text-sm text-green-400">신규 진입</span>
            </div>
            <div className="h-px flex-1 bg-slate-700"></div>
          </div>
          
          <div className="space-y-3">
            {newEntries.map((company, index) => (
              <button
                key={index}
                onClick={() => onViewProfile && onViewProfile(company.ticker)}
                className="w-full bg-slate-800/60 border border-green-700/30 rounded-xl p-3 hover:bg-slate-800 hover:border-green-600/50 hover:shadow-lg hover:shadow-green-500/10 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  {/* Company Logo */}
                  <div className="size-10 rounded-lg bg-white flex items-center justify-center overflow-hidden flex-shrink-0 group-hover:scale-110 transition-transform">
                    <img
                      src={company.logoUrl}
                      alt={company.name}
                      className="size-8 object-contain"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  </div>

                  {/* Company Info */}
                  <div className="flex-1 min-w-0 text-left">
                    <div className="text-slate-200 truncate group-hover:text-green-400 transition-colors">{company.name}</div>
                    <div className="text-xs text-slate-500">{company.ticker}</div>
                  </div>

                  {/* New Badge & Rank */}
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className="bg-gradient-to-r from-green-500 to-emerald-500 text-white text-xs px-2 py-0.5 rounded-full">
                      NEW
                    </span>
                    <span className="text-xs text-slate-400">#{company.rank}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Section B: Dropped Out (Red) */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-lg">
              <TrendingDown className="size-4 text-red-400" />
              <span className="text-sm text-red-400">순위 이탈</span>
            </div>
            <div className="h-px flex-1 bg-slate-700"></div>
          </div>
          
          <div className="space-y-3">
            {droppedOut.map((company, index) => (
              <button
                key={index}
                onClick={() => onViewProfile && onViewProfile(company.ticker)}
                className="w-full bg-slate-800/60 border border-red-700/30 rounded-xl p-3 hover:bg-slate-800 hover:border-red-600/50 hover:shadow-lg hover:shadow-red-500/10 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  {/* Company Logo */}
                  <div className="size-10 rounded-lg bg-white flex items-center justify-center overflow-hidden flex-shrink-0 group-hover:scale-110 transition-transform">
                    <img
                      src={company.logoUrl}
                      alt={company.name}
                      className="size-8 object-contain"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  </div>

                  {/* Company Info */}
                  <div className="flex-1 min-w-0 text-left">
                    <div className="text-slate-200 truncate group-hover:text-red-400 transition-colors">{company.name}</div>
                    <div className="text-xs text-slate-500">{company.ticker}</div>
                  </div>

                  {/* Out Badge & Previous Rank */}
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <span className="bg-gradient-to-r from-red-500 to-rose-500 text-white text-xs px-2 py-0.5 rounded-full">
                      OUT
                    </span>
                    <span className="text-xs text-slate-400 line-through">#{company.previousRank}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
      
      <div className="mt-6 pt-4 border-t border-slate-700">
        <p className="text-xs text-slate-400 text-center">
          최근 7일 순위 변동 현황
        </p>
      </div>
    </div>
  );
}