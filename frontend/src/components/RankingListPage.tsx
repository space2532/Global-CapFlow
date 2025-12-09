import { useState, useMemo, useEffect } from 'react';
import { Header } from './Header';
import { Search, Filter, TrendingUp, TrendingDown, Minus, Award, ChevronDown } from 'lucide-react';

interface RankingCompany {
  rank: number;
  name: string;
  ticker: string;
  logoUrl: string;
  marketCap: string;
  marketCapValue: number;
  sector: string;
  industry: string;
  country: string;
  countryCode: string;
  rankChange: number; // positive = up, negative = down, 0 = no change
  isNewEntry: boolean;
}

interface RankingListPageProps {
  onViewProfile?: (ticker: string) => void;
  sector?: string;
}

// Mock data for Top 100 companies
const generateCompanies = (): RankingCompany[] => {
  const sectors = ['기술', '금융', '헬스케어', '에너지', '소비재', '산업재', '통신', '부동산', '유틸리티', '소재', '반도체'];
  const countries = [
    { name: '미국', code: 'US', flag: '🇺🇸' },
    { name: '중국', code: 'CN', flag: '🇨🇳' },
    { name: '한국', code: 'KR', flag: '🇰🇷' },
    { name: '일본', code: 'JP', flag: '🇯🇵' },
    { name: '영국', code: 'GB', flag: '🇬🇧' },
    { name: '프랑스', code: 'FR', flag: '🇫🇷' },
    { name: '독일', code: 'DE', flag: '🇩🇪' },
    { name: '사우디', code: 'SA', flag: '🇸🇦' },
    { name: '네덜란드', code: 'NL', flag: '🇳🇱' },
    { name: '스위스', code: 'CH', flag: '🇨🇭' },
  ];

  const companyNames = [
    { name: 'Apple Inc.', ticker: 'AAPL', url: 'apple.com', industry: '소비자 전자제품', country: countries[0] },
    { name: 'Microsoft Corp.', ticker: 'MSFT', url: 'microsoft.com', industry: '소프트웨어', country: countries[0] },
    { name: 'Saudi Aramco', ticker: 'ARAMCO', url: 'aramco.com', industry: '석유 & 가스', country: countries[7] },
    { name: 'Alphabet Inc.', ticker: 'GOOGL', url: 'google.com', industry: '인터넷 서비스', country: countries[0] },
    { name: 'Amazon.com', ticker: 'AMZN', url: 'amazon.com', industry: '전자상거래', country: countries[0] },
    { name: 'NVIDIA Corp.', ticker: 'NVDA', url: 'nvidia.com', industry: 'GPU 제조', country: countries[0] },
    { name: 'Tesla Inc.', ticker: 'TSLA', url: 'tesla.com', industry: '전기차', country: countries[0] },
    { name: 'Meta Platforms', ticker: 'META', url: 'meta.com', industry: '소셜 미디어', country: countries[0] },
    { name: 'Berkshire Hathaway', ticker: 'BRK.B', url: 'berkshirehathaway.com', industry: '투자 회사', country: countries[0] },
    { name: 'TSMC', ticker: 'TSM', url: 'tsmc.com', industry: '반도체 제조', country: countries[1] },
    { name: 'Visa Inc.', ticker: 'V', url: 'visa.com', industry: '결제 서비스', country: countries[0] },
    { name: 'JPMorgan Chase', ticker: 'JPM', url: 'jpmorganchase.com', industry: '은행', country: countries[0] },
    { name: 'Samsung Electronics', ticker: '005930.KS', url: 'samsung.com', industry: '전자제품', country: countries[2] },
    { name: 'Johnson & Johnson', ticker: 'JNJ', url: 'jnj.com', industry: '제약 & 헬스케어', country: countries[0] },
    { name: 'UnitedHealth Group', ticker: 'UNH', url: 'unitedhealthgroup.com', industry: '건강보험', country: countries[0] },
    { name: 'Walmart Inc.', ticker: 'WMT', url: 'walmart.com', industry: '소매', country: countries[0] },
    { name: 'Mastercard Inc.', ticker: 'MA', url: 'mastercard.com', industry: '결제 서비스', country: countries[0] },
    { name: 'Exxon Mobil', ticker: 'XOM', url: 'exxonmobil.com', industry: '석유 & 가스', country: countries[0] },
    { name: 'Procter & Gamble', ticker: 'PG', url: 'pg.com', industry: '소비재', country: countries[0] },
    { name: 'LVMH', ticker: 'MC.PA', url: 'lvmh.com', industry: '명품', country: countries[5] },
    { name: 'Eli Lilly', ticker: 'LLY', url: 'lilly.com', industry: '제약', country: countries[0] },
    { name: 'Novo Nordisk', ticker: 'NVO', url: 'novonordisk.com', industry: '제약', country: countries[0] },
    { name: 'ASML Holding', ticker: 'ASML', url: 'asml.com', industry: '반도체 장비', country: countries[8] },
    { name: 'Tencent Holdings', ticker: 'TCEHY', url: 'tencent.com', industry: '인터넷 서비스', country: countries[1] },
    { name: 'Toyota Motor', ticker: 'TM', url: 'toyota.com', industry: '자동차', country: countries[3] },
    { name: 'Nestlé', ticker: 'NSRGY', url: 'nestle.com', industry: '식품 & 음료', country: countries[9] },
    { name: 'Home Depot', ticker: 'HD', url: 'homedepot.com', industry: '가정용품 소매', country: countries[0] },
    { name: 'Chevron Corp.', ticker: 'CVX', url: 'chevron.com', industry: '석유 & 가스', country: countries[0] },
    { name: 'AbbVie Inc.', ticker: 'ABBV', url: 'abbvie.com', industry: '제약', country: countries[0] },
    { name: 'Broadcom Inc.', ticker: 'AVGO', url: 'broadcom.com', industry: '반도체', country: countries[0] },
    { name: 'Oracle Corp.', ticker: 'ORCL', url: 'oracle.com', industry: '소프트웨어', country: countries[0] },
    { name: 'Coca-Cola', ticker: 'KO', url: 'coca-cola.com', industry: '음료', country: countries[0] },
    { name: 'Bank of America', ticker: 'BAC', url: 'bankofamerica.com', industry: '은행', country: countries[0] },
    { name: 'PepsiCo', ticker: 'PEP', url: 'pepsico.com', industry: '식품 & 음료', country: countries[0] },
    { name: 'Shell', ticker: 'SHEL', url: 'shell.com', industry: '석유 & 가스', country: countries[4] },
    { name: 'Adobe Inc.', ticker: 'ADBE', url: 'adobe.com', industry: '소프트웨어', country: countries[0] },
    { name: 'Salesforce', ticker: 'CRM', url: 'salesforce.com', industry: '클라우드 소프트웨어', country: countries[0] },
    { name: 'Merck & Co.', ticker: 'MRK', url: 'merck.com', industry: '제약', country: countries[0] },
    { name: 'Costco Wholesale', ticker: 'COST', url: 'costco.com', industry: '도매 소매', country: countries[0] },
    { name: 'Netflix Inc.', ticker: 'NFLX', url: 'netflix.com', industry: '스트리밍', country: countries[0] },
    { name: 'Accenture', ticker: 'ACN', url: 'accenture.com', industry: 'IT 컨설팅', country: countries[0] },
    { name: 'McDonald\'s', ticker: 'MCD', url: 'mcdonalds.com', industry: '외식', country: countries[0] },
    { name: 'Cisco Systems', ticker: 'CSCO', url: 'cisco.com', industry: '네트워크 장비', country: countries[0] },
    { name: 'Pfizer Inc.', ticker: 'PFE', url: 'pfizer.com', industry: '제약', country: countries[0] },
    { name: 'AMD', ticker: 'AMD', url: 'amd.com', industry: '반도체', country: countries[0] },
    { name: 'Nike Inc.', ticker: 'NKE', url: 'nike.com', industry: '스포츠 용품', country: countries[0] },
    { name: 'Thermo Fisher', ticker: 'TMO', url: 'thermofisher.com', industry: '과학 기기', country: countries[0] },
    { name: 'Danaher Corp.', ticker: 'DHR', url: 'danaher.com', industry: '과학 기기', country: countries[0] },
    { name: 'Abbott Labs', ticker: 'ABT', url: 'abbott.com', industry: '의료 기기', country: countries[0] },
    { name: 'Comcast Corp.', ticker: 'CMCSA', url: 'comcast.com', industry: '통신', country: countries[0] },
    { name: 'Verizon', ticker: 'VZ', url: 'verizon.com', industry: '통신', country: countries[0] },
    { name: 'AT&T Inc.', ticker: 'T', url: 'att.com', industry: '통신', country: countries[0] },
    { name: 'Intel Corp.', ticker: 'INTC', url: 'intel.com', industry: '반도체', country: countries[0] },
    { name: 'Qualcomm', ticker: 'QCOM', url: 'qualcomm.com', industry: '반도체', country: countries[0] },
    { name: 'Texas Instruments', ticker: 'TXN', url: 'ti.com', industry: '반도체', country: countries[0] },
    { name: 'Union Pacific', ticker: 'UNP', url: 'up.com', industry: '철도', country: countries[0] },
    { name: 'Honeywell', ticker: 'HON', url: 'honeywell.com', industry: '산업 복합기업', country: countries[0] },
    { name: 'Boeing Co.', ticker: 'BA', url: 'boeing.com', industry: '항공우주', country: countries[0] },
    { name: 'Caterpillar', ticker: 'CAT', url: 'caterpillar.com', industry: '건설 장비', country: countries[0] },
    { name: 'General Electric', ticker: 'GE', url: 'ge.com', industry: '산업 복합기업', country: countries[0] },
    { name: '3M Company', ticker: 'MMM', url: '3m.com', industry: '산업재', country: countries[0] },
    { name: 'Lockheed Martin', ticker: 'LMT', url: 'lockheedmartin.com', industry: '항공우주 & 방위', country: countries[0] },
    { name: 'American Express', ticker: 'AXP', url: 'americanexpress.com', industry: '금융 서비스', country: countries[0] },
    { name: 'Goldman Sachs', ticker: 'GS', url: 'goldmansachs.com', industry: '투자 은행', country: countries[0] },
    { name: 'Morgan Stanley', ticker: 'MS', url: 'morganstanley.com', industry: '투자 은행', country: countries[0] },
    { name: 'BlackRock', ticker: 'BLK', url: 'blackrock.com', industry: '자산 운용', country: countries[0] },
    { name: 'Charles Schwab', ticker: 'SCHW', url: 'schwab.com', industry: '증권', country: countries[0] },
    { name: 'Starbucks', ticker: 'SBUX', url: 'starbucks.com', industry: '외식', country: countries[0] },
    { name: 'Linde plc', ticker: 'LIN', url: 'linde.com', industry: '산업 가스', country: countries[4] },
    { name: 'Bristol Myers', ticker: 'BMY', url: 'bms.com', industry: '제약', country: countries[0] },
    { name: 'CVS Health', ticker: 'CVS', url: 'cvshealth.com', industry: '헬스케어 소매', country: countries[0] },
    { name: 'Siemens AG', ticker: 'SIEGY', url: 'siemens.com', industry: '산업 복합기업', country: countries[6] },
    { name: 'SAP SE', ticker: 'SAP', url: 'sap.com', industry: '소프트웨어', country: countries[6] },
    { name: 'Alibaba Group', ticker: 'BABA', url: 'alibaba.com', industry: '전자상거래', country: countries[1] },
    { name: 'Hermès', ticker: 'RMS.PA', url: 'hermes.com', industry: '명품', country: countries[5] },
    { name: 'L\'Oréal', ticker: 'OR.PA', url: 'loreal.com', industry: '화장품', country: countries[5] },
    { name: 'HSBC Holdings', ticker: 'HSBC', url: 'hsbc.com', industry: '은행', country: countries[4] },
    { name: 'AstraZeneca', ticker: 'AZN', url: 'astrazeneca.com', industry: '제약', country: countries[4] },
    { name: 'Unilever', ticker: 'UL', url: 'unilever.com', industry: '소비재', country: countries[4] },
    { name: 'Roche Holding', ticker: 'RHHBY', url: 'roche.com', industry: '제약', country: countries[9] },
    { name: 'Novartis AG', ticker: 'NVS', url: 'novartis.com', industry: '제약', country: countries[9] },
    { name: 'Sony Group', ticker: 'SONY', url: 'sony.com', industry: '전자제품', country: countries[3] },
    { name: 'SoftBank Group', ticker: '9984.T', url: 'softbank.jp', industry: '통신 & 투자', country: countries[3] },
    { name: 'BYD Company', ticker: 'BYDDY', url: 'byd.com', industry: '전기차', country: countries[1] },
    { name: 'Meituan', ticker: 'MPNGY', url: 'meituan.com', industry: '배달 & 서비스', country: countries[1] },
    { name: 'Pinduoduo', ticker: 'PDD', url: 'pinduoduo.com', industry: '전자상거래', country: countries[1] },
    { name: 'ICBC', ticker: 'IDCBY', url: 'icbc.com.cn', industry: '은행', country: countries[1] },
    { name: 'China Construction', ticker: 'CICHY', url: 'ccb.com', industry: '은행', country: countries[1] },
    { name: 'Hyundai Motor', ticker: '005380.KS', url: 'hyundai.com', industry: '자동차', country: countries[2] },
    { name: 'SK Hynix', ticker: '000660.KS', url: 'skhynix.com', industry: '반도체', country: countries[2] },
    { name: 'LG Energy', ticker: '373220.KS', url: 'lgensol.com', industry: '배터리', country: countries[2] },
    { name: 'POSCO Holdings', ticker: '005490.KS', url: 'posco.com', industry: '철강', country: countries[2] },
    { name: 'Naver Corp.', ticker: '035420.KS', url: 'naver.com', industry: '인터넷 서비스', country: countries[2] },
    { name: 'Kakao Corp.', ticker: '035720.KS', url: 'kakao.com', industry: '인터넷 서비스', country: countries[2] },
    { name: 'Rio Tinto', ticker: 'RIO', url: 'riotinto.com', industry: '광업', country: countries[4] },
    { name: 'BHP Group', ticker: 'BHP', url: 'bhp.com', industry: '광업', country: countries[0] },
    { name: 'Airbus SE', ticker: 'EADSY', url: 'airbus.com', industry: '항공우주', country: countries[5] },
    { name: 'Ferrari N.V.', ticker: 'RACE', url: 'ferrari.com', industry: '자동차', country: countries[0] },
    { name: 'IBM Corp.', ticker: 'IBM', url: 'ibm.com', industry: '소프트웨어 & IT 서비스', country: countries[0] },
    { name: 'Uber Technologies', ticker: 'UBER', url: 'uber.com', industry: '차량 공유 & 배달', country: countries[0] },
  ];

  return companyNames.map((company, index) => {
    const rank = index + 1;
    let marketCapValue = 3200 - (rank * 28) - Math.random() * 20;
    if (marketCapValue < 50) marketCapValue = 50 + Math.random() * 100;
    
    const formatMarketCap = (value: number): string => {
      if (value >= 1000) return `$${(value / 1000).toFixed(1)}T`;
      return `$${value.toFixed(0)}B`;
    };

    // Determine sector based on industry
    let sector = '기술';
    if (company.industry.includes('제약') || company.industry.includes('헬스케어') || company.industry.includes('의료')) {
      sector = '헬스케어';
    } else if (company.industry.includes('은행') || company.industry.includes('금융') || company.industry.includes('투자') || company.industry.includes('증권')) {
      sector = '금융';
    } else if (company.industry.includes('석유') || company.industry.includes('가스') || company.industry.includes('에너지')) {
      sector = '에너지';
    } else if (company.industry.includes('소매') || company.industry.includes('소비재') || company.industry.includes('식품') || company.industry.includes('음료') || company.industry.includes('명품') || company.industry.includes('외식')) {
      sector = '소비재';
    } else if (company.industry.includes('통신')) {
      sector = '통신';
    } else if (company.industry.includes('반도체')) {
      sector = '반도체';
    } else if (company.industry.includes('산업') || company.industry.includes('건설') || company.industry.includes('항공') || company.industry.includes('철도') || company.industry.includes('광업') || company.industry.includes('철강')) {
      sector = '산업재';
    }

    // Generate rank change: -10 to +10, with bias towards 0
    let rankChange = Math.floor(Math.random() * 21) - 10;
    if (Math.abs(rankChange) <= 2 && Math.random() > 0.3) {
      rankChange = 0;
    }

    // Mark new entries (5% chance)
    const isNewEntry = Math.random() < 0.05;

    return {
      rank,
      name: company.name,
      ticker: company.ticker,
      logoUrl: `https://logo.clearbit.com/${company.url}`,
      marketCap: formatMarketCap(marketCapValue),
      marketCapValue,
      sector,
      industry: company.industry,
      country: company.country.name,
      countryCode: company.country.flag,
      rankChange: isNewEntry ? 999 : rankChange, // 999 for new entries
      isNewEntry,
    };
  });
};

const allCompanies = generateCompanies();
const allSectors = ['전체', ...Array.from(new Set(allCompanies.map(c => c.sector))).sort()];

function getRankChangeIcon(change: number) {
  if (change === 999) return { icon: Award, color: 'text-green-400', label: 'NEW' };
  if (change > 0) return { icon: TrendingUp, color: 'text-green-400', label: `+${change}` };
  if (change < 0) return { icon: TrendingDown, color: 'text-red-400', label: `${change}` };
  return { icon: Minus, color: 'text-slate-500', label: '—' };
}

export function RankingListPage({ onViewProfile, sector }: RankingListPageProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>(sector || '전체');

  // Normalize sector name (map "기술/IT" to "기술", etc.)
  const normalizeSector = (sectorName: string): string => {
    if (sectorName === '기술/IT') return '기술';
    return sectorName;
  };

  const filteredCompanies = useMemo(() => {
    return allCompanies.filter(company => {
      const matchesSearch = searchQuery === '' ||
        company.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        company.ticker.toLowerCase().includes(searchQuery.toLowerCase());
      
      const normalizedSelected = normalizeSector(selectedSector);
      const matchesSector = selectedSector === '전체' || company.sector === normalizedSelected;
      
      return matchesSearch && matchesSector;
    });
  }, [searchQuery, selectedSector]);

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
        {/* Data Table - Desktop */}
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
                          <div className="size-10 rounded-full bg-white flex items-center justify-center flex-shrink-0 overflow-hidden">
                            <img
                              src={company.logoUrl}
                              alt={company.name}
                              className="size-8 object-contain"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          </div>
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
                        <span className="text-2xl" title={company.country}>{company.countryCode}</span>
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

        {/* Mobile Card List */}
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
                      <div className="size-8 rounded-lg bg-white flex items-center justify-center overflow-hidden flex-shrink-0">
                        <img
                          src={company.logoUrl}
                          alt={company.name}
                          className="size-6 object-contain"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      </div>
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
                    <div className="flex items-center gap-1">
                      <span className="text-xl">{company.countryCode}</span>
                      <span className="text-sm text-slate-400">{company.country}</span>
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

        {/* Empty State */}
        {filteredCompanies.length === 0 && (
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