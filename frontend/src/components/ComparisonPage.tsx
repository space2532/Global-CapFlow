import { useState, useMemo } from 'react';
import { Header } from './Header';
import { Search, X, Zap, ArrowLeft, TrendingUp, DollarSign, Brain, BarChart3, Shield, Sparkles, Check } from 'lucide-react';

interface Company {
  id: string;
  name: string;
  ticker: string;
  logoUrl: string;
  sector: string;
  rank: number;
}

interface ComparisonData {
  marketCapComparison: string;
  aiGrowthPotential: string;
  financialHealth: string;
  competitiveAdvantage: string;
  riskAssessment: string;
  investmentRecommendation: string;
}

// Generate Top 100 companies
const generateTopCompanies = (): Company[] => {
  const companiesData = [
    { name: 'Apple Inc.', ticker: 'AAPL', url: 'apple.com', sector: '기술' },
    { name: 'Microsoft Corp.', ticker: 'MSFT', url: 'microsoft.com', sector: '기술' },
    { name: 'Alphabet Inc.', ticker: 'GOOGL', url: 'google.com', sector: '기술' },
    { name: 'Amazon.com', ticker: 'AMZN', url: 'amazon.com', sector: '기술' },
    { name: 'NVIDIA Corp.', ticker: 'NVDA', url: 'nvidia.com', sector: '기술' },
    { name: 'Tesla Inc.', ticker: 'TSLA', url: 'tesla.com', sector: '산업재' },
    { name: 'Meta Platforms', ticker: 'META', url: 'meta.com', sector: '기술' },
    { name: 'Berkshire Hathaway', ticker: 'BRK.B', url: 'berkshirehathaway.com', sector: '금융' },
    { name: 'TSMC', ticker: 'TSM', url: 'tsmc.com', sector: '반도체' },
    { name: 'Visa Inc.', ticker: 'V', url: 'visa.com', sector: '금융' },
    { name: 'JPMorgan Chase', ticker: 'JPM', url: 'jpmorganchase.com', sector: '금융' },
    { name: 'Samsung Electronics', ticker: '005930.KS', url: 'samsung.com', sector: '반도체' },
    { name: 'Johnson & Johnson', ticker: 'JNJ', url: 'jnj.com', sector: '헬스케어' },
    { name: 'UnitedHealth Group', ticker: 'UNH', url: 'unitedhealthgroup.com', sector: '헬스케어' },
    { name: 'Walmart Inc.', ticker: 'WMT', url: 'walmart.com', sector: '소비재' },
    { name: 'Mastercard Inc.', ticker: 'MA', url: 'mastercard.com', sector: '금융' },
    { name: 'Exxon Mobil', ticker: 'XOM', url: 'exxonmobil.com', sector: '에너지' },
    { name: 'Procter & Gamble', ticker: 'PG', url: 'pg.com', sector: '소비재' },
    { name: 'LVMH', ticker: 'MC.PA', url: 'lvmh.com', sector: '소비재' },
    { name: 'Netflix Inc.', ticker: 'NFLX', url: 'netflix.com', sector: '기술' },
    { name: 'Adobe Inc.', ticker: 'ADBE', url: 'adobe.com', sector: '기술' },
    { name: 'Salesforce', ticker: 'CRM', url: 'salesforce.com', sector: '기술' },
    { name: 'Intel Corp.', ticker: 'INTC', url: 'intel.com', sector: '반도체' },
    { name: 'AMD', ticker: 'AMD', url: 'amd.com', sector: '반도체' },
    { name: 'Nike Inc.', ticker: 'NKE', url: 'nike.com', sector: '소비재' },
    { name: 'Coca-Cola', ticker: 'KO', url: 'coca-cola.com', sector: '소비재' },
    { name: 'PepsiCo', ticker: 'PEP', url: 'pepsico.com', sector: '소비재' },
    { name: 'Oracle Corp.', ticker: 'ORCL', url: 'oracle.com', sector: '기술' },
    { name: 'Broadcom Inc.', ticker: 'AVGO', url: 'broadcom.com', sector: '반도체' },
    { name: 'AbbVie Inc.', ticker: 'ABBV', url: 'abbvie.com', sector: '헬스케어' },
    { name: 'Chevron Corp.', ticker: 'CVX', url: 'chevron.com', sector: '에너지' },
    { name: 'Bank of America', ticker: 'BAC', url: 'bankofamerica.com', sector: '금융' },
    { name: 'Eli Lilly', ticker: 'LLY', url: 'lilly.com', sector: '헬스케어' },
    { name: 'Costco Wholesale', ticker: 'COST', url: 'costco.com', sector: '소비재' },
    { name: 'Novo Nordisk', ticker: 'NVO', url: 'novonordisk.com', sector: '헬스케어' },
    { name: 'ASML Holding', ticker: 'ASML', url: 'asml.com', sector: '반도체' },
    { name: 'Tencent Holdings', ticker: 'TCEHY', url: 'tencent.com', sector: '기술' },
    { name: 'Toyota Motor', ticker: 'TM', url: 'toyota.com', sector: '산업재' },
    { name: 'Nestlé', ticker: 'NSRGY', url: 'nestle.com', sector: '소비재' },
    { name: 'Home Depot', ticker: 'HD', url: 'homedepot.com', sector: '소비재' },
    { name: 'Merck & Co.', ticker: 'MRK', url: 'merck.com', sector: '헬스케어' },
    { name: 'Accenture', ticker: 'ACN', url: 'accenture.com', sector: '기술' },
    { name: 'McDonald\'s', ticker: 'MCD', url: 'mcdonalds.com', sector: '소비재' },
    { name: 'Cisco Systems', ticker: 'CSCO', url: 'cisco.com', sector: '기술' },
    { name: 'Pfizer Inc.', ticker: 'PFE', url: 'pfizer.com', sector: '헬스케어' },
    { name: 'Thermo Fisher', ticker: 'TMO', url: 'thermofisher.com', sector: '헬스케어' },
    { name: 'Danaher Corp.', ticker: 'DHR', url: 'danaher.com', sector: '헬스케어' },
    { name: 'Abbott Labs', ticker: 'ABT', url: 'abbott.com', sector: '헬스케어' },
    { name: 'Comcast Corp.', ticker: 'CMCSA', url: 'comcast.com', sector: '통신' },
    { name: 'Verizon', ticker: 'VZ', url: 'verizon.com', sector: '통신' },
    { name: 'AT&T Inc.', ticker: 'T', url: 'att.com', sector: '통신' },
    { name: 'Qualcomm', ticker: 'QCOM', url: 'qualcomm.com', sector: '반도체' },
    { name: 'Texas Instruments', ticker: 'TXN', url: 'ti.com', sector: '반도체' },
    { name: 'Union Pacific', ticker: 'UNP', url: 'up.com', sector: '산업재' },
    { name: 'Honeywell', ticker: 'HON', url: 'honeywell.com', sector: '산업재' },
    { name: 'Boeing Co.', ticker: 'BA', url: 'boeing.com', sector: '산업재' },
    { name: 'Caterpillar', ticker: 'CAT', url: 'caterpillar.com', sector: '산업재' },
    { name: 'General Electric', ticker: 'GE', url: 'ge.com', sector: '산업재' },
    { name: '3M Company', ticker: 'MMM', url: '3m.com', sector: '산업재' },
    { name: 'Lockheed Martin', ticker: 'LMT', url: 'lockheedmartin.com', sector: '산업재' },
    { name: 'American Express', ticker: 'AXP', url: 'americanexpress.com', sector: '금융' },
    { name: 'Goldman Sachs', ticker: 'GS', url: 'goldmansachs.com', sector: '금융' },
    { name: 'Morgan Stanley', ticker: 'MS', url: 'morganstanley.com', sector: '금융' },
    { name: 'BlackRock', ticker: 'BLK', url: 'blackrock.com', sector: '금융' },
    { name: 'Charles Schwab', ticker: 'SCHW', url: 'schwab.com', sector: '금융' },
    { name: 'Starbucks', ticker: 'SBUX', url: 'starbucks.com', sector: '소비재' },
    { name: 'Linde plc', ticker: 'LIN', url: 'linde.com', sector: '산업재' },
    { name: 'Bristol Myers', ticker: 'BMY', url: 'bms.com', sector: '헬스케어' },
    { name: 'CVS Health', ticker: 'CVS', url: 'cvshealth.com', sector: '헬스케어' },
    { name: 'Siemens AG', ticker: 'SIEGY', url: 'siemens.com', sector: '산업재' },
    { name: 'SAP SE', ticker: 'SAP', url: 'sap.com', sector: '기술' },
    { name: 'Alibaba Group', ticker: 'BABA', url: 'alibaba.com', sector: '기술' },
    { name: 'Hermès', ticker: 'RMS.PA', url: 'hermes.com', sector: '소비재' },
    { name: 'L\'Oréal', ticker: 'OR.PA', url: 'loreal.com', sector: '소비재' },
    { name: 'HSBC Holdings', ticker: 'HSBC', url: 'hsbc.com', sector: '금융' },
    { name: 'AstraZeneca', ticker: 'AZN', url: 'astrazeneca.com', sector: '헬스케어' },
    { name: 'Unilever', ticker: 'UL', url: 'unilever.com', sector: '소비재' },
    { name: 'Roche Holding', ticker: 'RHHBY', url: 'roche.com', sector: '헬스케어' },
    { name: 'Novartis AG', ticker: 'NVS', url: 'novartis.com', sector: '헬스케어' },
    { name: 'Sony Group', ticker: 'SONY', url: 'sony.com', sector: '기술' },
    { name: 'SoftBank Group', ticker: '9984.T', url: 'softbank.jp', sector: '기술' },
    { name: 'BYD Company', ticker: 'BYDDY', url: 'byd.com', sector: '산업재' },
    { name: 'Meituan', ticker: 'MPNGY', url: 'meituan.com', sector: '기술' },
    { name: 'Pinduoduo', ticker: 'PDD', url: 'pinduoduo.com', sector: '기술' },
    { name: 'ICBC', ticker: 'IDCBY', url: 'icbc.com.cn', sector: '금융' },
    { name: 'China Construction', ticker: 'CICHY', url: 'ccb.com', sector: '금융' },
    { name: 'Hyundai Motor', ticker: '005380.KS', url: 'hyundai.com', sector: '산업재' },
    { name: 'SK Hynix', ticker: '000660.KS', url: 'skhynix.com', sector: '반도체' },
    { name: 'LG Energy', ticker: '373220.KS', url: 'lgensol.com', sector: '에너지' },
    { name: 'POSCO Holdings', ticker: '005490.KS', url: 'posco.com', sector: '산업재' },
    { name: 'Naver Corp.', ticker: '035420.KS', url: 'naver.com', sector: '기술' },
    { name: 'Kakao Corp.', ticker: '035720.KS', url: 'kakao.com', sector: '기술' },
    { name: 'Rio Tinto', ticker: 'RIO', url: 'riotinto.com', sector: '산업재' },
    { name: 'BHP Group', ticker: 'BHP', url: 'bhp.com', sector: '산업재' },
    { name: 'Airbus SE', ticker: 'EADSY', url: 'airbus.com', sector: '산업재' },
    { name: 'Ferrari N.V.', ticker: 'RACE', url: 'ferrari.com', sector: '산업재' },
    { name: 'Shell', ticker: 'SHEL', url: 'shell.com', sector: '에너지' },
    { name: 'TotalEnergies', ticker: 'TTE', url: 'totalenergies.com', sector: '에너지' },
    { name: 'IBM Corp.', ticker: 'IBM', url: 'ibm.com', sector: '기술' },
    { name: 'Uber Technologies', ticker: 'UBER', url: 'uber.com', sector: '기술' },
  ];

  return companiesData.map((company, index) => ({
    id: `company-${index + 1}`,
    name: company.name,
    ticker: company.ticker,
    logoUrl: `https://logo.clearbit.com/${company.url}`,
    sector: company.sector,
    rank: index + 1,
  }));
};

const allCompanies = generateTopCompanies();

// Extract unique sectors
const allSectors = ['전체', ...Array.from(new Set(allCompanies.map(c => c.sector))).sort()];

// Mock AI comparison generator
function generateComparison(company1: Company, company2: Company): ComparisonData {
  return {
    marketCapComparison: `${company1.name}과 ${company2.name}의 시가총액을 비교하면, 두 기업 모두 각자의 산업에서 지배적인 위치를 차지하고 있습니다. ${company1.name}은 강력한 브랜드 가치와 충성도 높은 고객 기반을 보유하고 있으며, ${company2.name}은 혁신적인 기술력과 시장 확장성을 바탕으로 지속적인 성장을 이어가고 있습니다.\n\n과거 5년간의 시가총액 변화를 분석하면, ${company1.name}은 연평균 15-20%의 성장률을 기록했으며, ${company2.name}은 20-25%의 더 높은 성장세를 보였습니다. 이는 ${company2.name}이 새로운 시장 기회를 더 적극적으로 포착하고 있음을 시사합니다.`,
    
    aiGrowthPotential: `AI 기술 통합 측면에서 두 기업은 서로 다른 접근 방식을 취하고 있습니다. ${company1.name}은 AI를 기존 제품 라인에 통합하여 사용자 경험을 향상시키는 데 집중하고 있으며, ${company2.name}은 AI를 핵심 경쟁력으로 활용하여 새로운 시장을 개척하고 있습니다.\n\n${company1.name}의 AI 관련 R&D 투자는 전체 매출의 약 8-10%를 차지하며, ${company2.name}은 12-15%로 더 높은 비율을 보이고 있습니다. 향후 3-5년간 AI 기술이 가져올 성장 잠재력을 고려할 때, ${company2.name}이 더 공격적인 성장 전략을 추구하고 있다고 평가됩니다.\n\n특히 생성형 AI, 자율주행, 그리고 산업용 AI 솔루션 분야에서 두 기업 모두 중요한 발전을 이루고 있으며, 이는 장기적인 수익 창출의 핵심 동력이 될 것으로 예상됩니다.`,
    
    financialHealth: `재무 건전성 측면에서 두 기업 모두 업계 최고 수준의 지표를 보유하고 있습니다.\n\n${company1.name}의 주요 재무 지표:\n• 부채비율: 35-40% (낮은 수준의 안정적 레버리지)\n• 현금 보유액: 600-800억 달러\n• 영업이익률: 25-30%\n• ROE: 45-55%\n\n${company2.name}의 주요 재무 지표:\n• 부채비율: 25-30% (매우 보수적인 재무 구조)\n• 현금 보유액: 400-600억 달러\n• 영업이익률: 30-35%\n• ROE: 50-60%\n\n두 기업 모두 강력한 현금 흐름 창출 능력을 보유하고 있으며, 배당금 지급과 자사주 매입을 통해 주주 가치를 적극적으로 환원하고 있습니다. ${company2.name}이 상대적으로 더 높은 수익성을 보이고 있으나, ${company1.name}의 안정적인 재무 구조도 매우 우수한 수준입니다.`,
    
    competitiveAdvantage: `${company1.name}의 핵심 경쟁우위는 브랜드 파워, 생태계 통합력, 그리고 고객 충성도에 있습니다. 수십 년간 구축된 브랜드 가치는 프리미엄 가격 전략을 가능하게 하며, 이는 업계 최고 수준의 마진율로 이어집니다.\n\n${company2.name}의 경쟁우위는 기술 혁신력, 시장 선점 능력, 그리고 규모의 경제에 있습니다. 지속적인 R&D 투자를 통해 차세대 기술을 선도하고 있으며, 이는 장기적인 시장 지배력을 강화합니다.\n\n두 기업 모두 높은 진입 장벽과 전환 비용을 형성하고 있어, 경쟁사의 시장 침투가 매우 어려운 구조를 갖추고 있습니다. 특히 네트워크 효과와 데이터 축적은 시간이 지날수록 경쟁우위를 더욱 공고히 하는 요소입니다.`,
    
    riskAssessment: `${company1.name}의 주요 리스크 요인:\n• 특정 제품군에 대한 높은 의존도\n• 중국 시장에서의 지정학적 리스크\n• 규제 당국의 반독점 조사 가능성\n• 시장 포화도 증가에 따른 성장 둔화 우려\n\n${company2.name}의 주요 리스크 요인:\n• 급격한 기술 변화에 따른 사업 모델 변동성\n• 신규 경쟁자 등장으로 인한 시장 점유율 위협\n• 높은 성장 기대에 따른 밸류에이션 프리미엄 부담\n• 글로벌 경기 침체 시 수요 감소 가능성\n\n두 기업 모두 체계적인 리스크 관리 시스템을 갖추고 있으며, 다각화된 사업 포트폴리오를 통해 특정 시장의 변동성을 완화하고 있습니다.`,
    
    investmentRecommendation: `종합적인 투자 관점에서, 두 기업 모두 장기 투자자에게 매력적인 선택지입니다.\n\n${company1.name} 투자 추천:\n• 투자 성향: 안정적 성장과 배당 수익을 추구하는 보수적 투자자\n• 기대 수익률: 연 10-15% (중장기)\n• 핵심 논거: 검증된 비즈니스 모델, 강력한 브랜드 파워, 안정적 현금흐름\n\n${company2.name} 투자 추천:\n• 투자 성향: 높은 성장 잠재력을 추구하는 공격적 투자자\n• 기대 수익률: 연 15-25% (중장기)\n• 핵심 논거: 혁신적 기술력, 시장 확장 기회, AI 시대의 핵심 수혜주\n\n포트폴리오 전략 측면에서, 두 기업에 분산 투자하여 안정성과 성장성을 동시에 추구하는 것도 효과적인 접근법입니다. 현재 시장 밸류에이션을 고려할 때, ${company1.name}은 적정 가격 수준이며, ${company2.name}은 다소 프리미엄이 반영되어 있으나 성장 잠재력을 감안하면 합리적인 수준으로 판단됩니다.`
  };
}

export function ComparisonPage() {
  const [selectedCompanies, setSelectedCompanies] = useState<Company[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSector, setSelectedSector] = useState('전체');

  const handleSelectCompany = (company: Company) => {
    if (selectedCompanies.find(c => c.id === company.id)) {
      setSelectedCompanies(selectedCompanies.filter(c => c.id !== company.id));
    } else if (selectedCompanies.length < 2) {
      setSelectedCompanies([...selectedCompanies, company]);
    }
  };

  const handleAnalyze = () => {
    if (selectedCompanies.length === 2) {
      const data = generateComparison(selectedCompanies[0], selectedCompanies[1]);
      setComparisonData(data);
      setShowComparison(true);
    }
  };

  const handleBack = () => {
    setShowComparison(false);
    setSelectedCompanies([]);
    setComparisonData(null);
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
      .filter(company => selectedSector === '전체' || company.sector === selectedSector)
      .filter(company => 
        company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        company.ticker.toLowerCase().includes(searchTerm.toLowerCase())
      );
  }, [searchTerm, selectedSector]);

  // State 2: Comparison Result View (Split-screen)
  if (showComparison && comparisonData && selectedCompanies.length === 2) {
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
            {/* Market Cap Comparison */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-500/20 rounded-xl">
                  <DollarSign className="size-6 text-blue-400" />
                </div>
                <h3 className="text-2xl text-slate-100">시가총액 비교</h3>
              </div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                {comparisonData.marketCapComparison}
              </div>
            </div>

            {/* AI Growth Potential */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-500/20 rounded-xl">
                  <Brain className="size-6 text-purple-400" />
                </div>
                <h3 className="text-2xl text-slate-100">AI 성장 잠재력</h3>
              </div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                {comparisonData.aiGrowthPotential}
              </div>
            </div>

            {/* Financial Health */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-green-500/20 rounded-xl">
                  <BarChart3 className="size-6 text-green-400" />
                </div>
                <h3 className="text-2xl text-slate-100">재무 건전성</h3>
              </div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                {comparisonData.financialHealth}
              </div>
            </div>

            {/* Competitive Advantage */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-cyan-500/20 rounded-xl">
                  <TrendingUp className="size-6 text-cyan-400" />
                </div>
                <h3 className="text-2xl text-slate-100">경쟁 우위</h3>
              </div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                {comparisonData.competitiveAdvantage}
              </div>
            </div>

            {/* Risk Assessment */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-yellow-500/20 rounded-xl">
                  <Shield className="size-6 text-yellow-400" />
                </div>
                <h3 className="text-2xl text-slate-100">리스크 평가</h3>
              </div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                {comparisonData.riskAssessment}
              </div>
            </div>

            {/* Investment Recommendation */}
            <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/20 border border-blue-500/30 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-500/20 rounded-xl">
                  <Sparkles className="size-6 text-blue-400" />
                </div>
                <h3 className="text-2xl text-slate-100">투자 추천</h3>
              </div>
              <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                {comparisonData.investmentRecommendation}
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
        {/* Results Info */}
        <div className="mb-4 text-sm text-slate-400">
          {filteredCompanies.length}개 기업 표시 중
        </div>

        {/* Company Grid */}
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
                <div className="size-20 mx-auto mb-3 rounded-xl bg-white flex items-center justify-center overflow-hidden">
                  <img
                    src={company.logoUrl}
                    alt={company.name}
                    className="size-16 object-contain"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
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

        {/* Empty State */}
        {filteredCompanies.length === 0 && (
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
            disabled={selectedCompanies.length !== 2}
            className={`w-full max-w-md mx-auto flex items-center justify-center gap-3 px-8 py-5 rounded-2xl shadow-2xl transition-all duration-300 ${
              selectedCompanies.length === 2
                ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-blue-500/50 hover:scale-105 cursor-pointer'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            <Zap className={`size-6 ${selectedCompanies.length === 2 ? 'animate-pulse' : ''}`} />
            <span className="text-xl">
              비교하기 ({selectedCompanies.length}/2)
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}