import { Header } from './Header';
import { ArrowLeft, TrendingUp, TrendingDown, Activity, DollarSign, Building2, MapPin, Globe, Newspaper, ExternalLink } from 'lucide-react';

interface StockProfileProps {
  ticker: string;
  onBack?: () => void;
}

interface FinancialData {
  period: string;
  revenue: string;
  netIncome: string;
  per: string;
}

interface NewsItem {
  id: string;
  title: string;
  aiSummary: string;
  source: string;
  sourceUrl: string;
  publishedDate: string;
}

// Mock data for demonstration
const mockStockData = {
  ticker: 'AAPL',
  companyName: 'Apple Inc.',
  industry: '소비자 전자제품',
  sector: '기술',
  country: '미국',
  marketCap: '$3.2T',
  currentPrice: '$195.42',
  priceChange: '+2.35%',
  priceChangeValue: '+$4.48',
  isPositive: true,
  logoUrl: 'https://logo.clearbit.com/apple.com',
  
  // AI Report Data
  aiReport: {
    sentimentScore: 85,
    sentimentLabel: '긍정적',
    summaryContent: 'Apple은 강력한 브랜드 가치와 충성도 높은 고객 기반을 바탕으로 지속적인 성장을 보여주고 있습니다. iPhone 15 시리즈의 성공적인 출시와 서비스 부문의 안정적인 수익 증가가 주요 성장 동력입니다. Vision Pro의 출시는 공간 컴퓨팅 시장에서 새로운 기회를 제공하며, AI 기술 통합이 향후 제품 경쟁력을 강화할 것으로 예상됩니다.\n\n금융 건전성 측면에서 Apple은 업계 최고 수준의 현금 보유고와 안정적인 현금 흐름을 유지하고 있습니다. 주주 환원 정책도 적극적이며, 배당금 지급과 자사주 매입을 통해 주주 가치를 증대시키고 있습니다. 그러나 중국 시장에서의 경쟁 심화와 규제 리스크는 주의 깊게 모니터링해야 할 요소입니다.\n\n전반적으로 Apple은 안정적인 수익성과 혁신 능력을 겸비한 우량주로, 장기 투자자에게 매력적인 선택지입니다. 현재 밸류에이션은 다소 높은 편이나, 지속 가능한 성장 전망을 고려하면 합리적인 수준으로 평가됩니다.',
    
    quarterlyReport: '2024년 4분기 실적은 시장 예상을 상회했으며, 특히 서비스 부문에서 두 자릿수 성장을 기록했습니다. 아시아 태평양 지역의 매출 증가가 눈에 띄었으며, 웨어러블 기기 부문도 강세를 보였습니다. 경영진은 2025년 1분기 가이던스를 긍정적으로 제시했으며, AI 기능 탑재가 다음 제품 사이클의 핵심이 될 것으로 전망했습니다.'
  },
  
  // Financial Data
  financials: [
    { period: '2024 Q4', revenue: '$119.6B', netIncome: '$33.9B', per: '32.5' },
    { period: '2024 Q3', revenue: '$85.8B', netIncome: '$21.4B', per: '31.2' },
    { period: '2024 Q2', revenue: '$90.8B', netIncome: '$23.6B', per: '30.8' },
    { period: '2024 Q1', revenue: '$119.6B', netIncome: '$33.9B', per: '32.1' },
    { period: '2023 Q4', revenue: '$117.2B', netIncome: '$33.0B', per: '31.5' },
    { period: '2023 Q3', revenue: '$81.8B', netIncome: '$19.9B', per: '29.8' },
    { period: '2023 Q2', revenue: '$94.8B', netIncome: '$24.2B', per: '30.2' },
    { period: '2023 Q1', revenue: '$117.2B', netIncome: '$30.0B', per: '28.9' },
  ] as FinancialData[],
  
  // News Data
  news: [
    {
      id: '1',
      title: 'Apple Reports Q4 Earnings: Revenue Up 8.2%, Net Income Up 12.5%',
      aiSummary: 'Apple reported strong Q4 earnings with revenue up 8.2% and net income up 12.5% compared to the same period last year. The company\'s services segment saw double-digit growth, and the Asia-Pacific region showed significant revenue increases.',
      source: 'Bloomberg',
      sourceUrl: 'https://www.bloomberg.com/news/articles/2024-02-01/apple-reports-q4-earnings-revenue-up-8-2-net-income-up-12-5',
      publishedDate: '2024-02-01'
    },
    {
      id: '2',
      title: 'Apple Launches Vision Pro: A New Era in Spatial Computing',
      aiSummary: 'Apple unveiled Vision Pro, a revolutionary spatial computing device that combines advanced AI and augmented reality. The product is expected to open up new opportunities in the spatial computing market and enhance Apple\'s product lineup.',
      source: 'The Verge',
      sourceUrl: 'https://www.theverge.com/2024/1/10/27945656/apple-vision-pro-launch-spatial-computing',
      publishedDate: '2024-01-10'
    },
    {
      id: '3',
      title: 'Apple\'s iPhone 15 Series: A Strong Start to the New Year',
      aiSummary: 'The iPhone 15 series had a strong launch, meeting and exceeding market expectations. The new models received positive reviews for their design, performance, and features, contributing to Apple\'s continued market leadership in the smartphone industry.',
      source: 'CNET',
      sourceUrl: 'https://www.cnet.com/news/apple-iphone-15-series-launch-review/',
      publishedDate: '2023-09-12'
    }
  ] as NewsItem[]
};

function getSentimentColor(score: number): { bg: string; text: string; barBg: string } {
  if (score >= 80) return { bg: 'bg-green-500/20', text: 'text-green-400', barBg: 'bg-green-500' };
  if (score >= 60) return { bg: 'bg-blue-500/20', text: 'text-blue-400', barBg: 'bg-blue-500' };
  if (score >= 40) return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', barBg: 'bg-yellow-500' };
  return { bg: 'bg-red-500/20', text: 'text-red-400', barBg: 'bg-red-500' };
}

export function StockProfilePage({ ticker, onBack }: StockProfileProps) {
  const data = mockStockData;
  const sentimentColors = getSentimentColor(data.aiReport.sentimentScore);
  
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Sticky Header */}
      <div className="sticky top-0 z-50 bg-slate-950/95 backdrop-blur-sm border-b border-slate-800">
        <Header />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          {/* Back Button */}
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-slate-400 hover:text-blue-400 transition-colors mb-4"
            >
              <ArrowLeft className="size-5" />
              <span>돌아가기</span>
            </button>
          )}
          
          {/* Company Header */}
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex items-start gap-4">
              {/* Company Logo */}
              <div className="size-16 rounded-2xl bg-white flex items-center justify-center flex-shrink-0 overflow-hidden ring-2 ring-slate-700">
                <img
                  src={data.logoUrl}
                  alt={data.companyName}
                  className="size-14 object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
              
              {/* Company Name & Ticker */}
              <div className="flex-1">
                <h1 className="text-3xl text-slate-100 mb-1">
                  {data.companyName}
                </h1>
                <div className="flex items-center gap-2 mb-3">
                  <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm">
                    {data.ticker}
                  </span>
                </div>
                
                {/* Metadata Row */}
                <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Building2 className="size-4" />
                    <span>{data.industry}</span>
                  </div>
                  <span className="text-slate-700">•</span>
                  <div className="flex items-center gap-1.5">
                    <Activity className="size-4" />
                    <span>{data.sector}</span>
                  </div>
                  <span className="text-slate-700">•</span>
                  <div className="flex items-center gap-1.5">
                    <MapPin className="size-4" />
                    <span>{data.country}</span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Key Metrics */}
            <div className="flex flex-col sm:items-end gap-2">
              <div className="flex items-baseline gap-2">
                <span className="text-4xl text-slate-100">{data.currentPrice}</span>
                <div className={`flex items-center gap-1 ${data.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                  {data.isPositive ? (
                    <TrendingUp className="size-5" />
                  ) : (
                    <TrendingDown className="size-5" />
                  )}
                  <span className="text-lg">{data.priceChange}</span>
                </div>
              </div>
              <div className={`text-sm ${data.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                {data.priceChangeValue}
              </div>
              <div className="flex items-center gap-2 mt-2">
                <DollarSign className="size-4 text-slate-500" />
                <span className="text-sm text-slate-400">시가총액</span>
                <span className="text-lg text-slate-200">{data.marketCap}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">
        {/* AI Investment Report Section */}
        <div className="mb-8">
          <div className="bg-gradient-to-br from-blue-900/30 to-cyan-900/20 border border-blue-500/30 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-blue-500/20 rounded-xl">
                <Globe className="size-6 text-blue-400" />
              </div>
              <h2 className="text-2xl text-slate-100">AI 투자 리포트</h2>
            </div>
            
            {/* Sentiment Indicator */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-300">투자 심리 분석</span>
                <div className="flex items-center gap-2">
                  <span className={`text-2xl ${sentimentColors.text}`}>
                    {data.aiReport.sentimentScore}/100
                  </span>
                  <span className={`px-3 py-1 ${sentimentColors.bg} ${sentimentColors.text} rounded-lg text-sm`}>
                    {data.aiReport.sentimentLabel}
                  </span>
                </div>
              </div>
              
              {/* Sentiment Bar */}
              <div className="relative w-full h-3 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`absolute left-0 top-0 h-full ${sentimentColors.barBg} rounded-full transition-all duration-1000 ease-out`}
                  style={{ width: `${data.aiReport.sentimentScore}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20"></div>
                </div>
              </div>
            </div>
            
            {/* Summary Content */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg text-slate-200 mb-3">종합 분석</h3>
                <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                  {data.aiReport.summaryContent}
                </div>
              </div>
              
              <div>
                <h3 className="text-lg text-slate-200 mb-3">분기 실적 분석</h3>
                <div className="text-slate-300 leading-relaxed bg-slate-900/40 rounded-xl p-4 border border-slate-700/50">
                  {data.aiReport.quarterlyReport}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* AI News Briefing Section */}
        <div className="mb-8">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl shadow-xl overflow-hidden">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-700 rounded-xl">
                  <Newspaper className="size-5 text-slate-300" />
                </div>
                <div>
                  <h2 className="text-2xl text-slate-100">최신 뉴스 AI 요약</h2>
                  <p className="text-sm text-slate-400 mt-1">AI가 분석한 주요 뉴스 및 시장 동향</p>
                </div>
              </div>
            </div>
            
            {/* News Cards */}
            <div className="p-6 space-y-4">
              {data.news.map((newsItem) => (
                <div
                  key={newsItem.id}
                  className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-5 hover:border-slate-600 transition-all"
                >
                  {/* News Title */}
                  <h3 className="text-slate-100 mb-3 leading-snug">
                    {newsItem.title}
                  </h3>
                  
                  {/* AI Summary */}
                  <p className="text-slate-300 leading-relaxed mb-4 text-sm">
                    {newsItem.aiSummary}
                  </p>
                  
                  {/* Source Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
                    <a
                      href={newsItem.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors group"
                    >
                      <span>출처: {newsItem.source}</span>
                      <ExternalLink className="size-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                    </a>
                    <span className="text-xs text-slate-500">{newsItem.publishedDate}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Financials Table */}
        <div>
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl shadow-xl overflow-hidden">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-2xl text-slate-100">재무 데이터</h2>
              <p className="text-sm text-slate-400 mt-1">분기별 주요 재무 지표</p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-800/50 border-b border-slate-700">
                    <th className="px-6 py-4 text-left text-sm text-slate-300">기간</th>
                    <th className="px-6 py-4 text-right text-sm text-slate-300">매출액</th>
                    <th className="px-6 py-4 text-right text-sm text-slate-300">순이익</th>
                    <th className="px-6 py-4 text-right text-sm text-slate-300">PER</th>
                  </tr>
                </thead>
                <tbody>
                  {data.financials.map((row, index) => (
                    <tr
                      key={index}
                      className={`border-b border-slate-800 hover:bg-slate-800/50 transition-colors ${
                        index % 2 === 0 ? 'bg-slate-900/20' : 'bg-slate-900/40'
                      }`}
                    >
                      <td className="px-6 py-4 text-slate-200">{row.period}</td>
                      <td className="px-6 py-4 text-right text-slate-200">{row.revenue}</td>
                      <td className="px-6 py-4 text-right text-slate-200">{row.netIncome}</td>
                      <td className="px-6 py-4 text-right text-slate-200">{row.per}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Table Footer Summary */}
            <div className="px-6 py-4 bg-slate-800/30 border-t border-slate-700">
              <div className="flex flex-wrap gap-6 text-sm">
                <div>
                  <span className="text-slate-400">평균 PER: </span>
                  <span className="text-slate-200">30.75</span>
                </div>
                <div>
                  <span className="text-slate-400">YoY 매출 성장: </span>
                  <span className="text-green-400">+8.2%</span>
                </div>
                <div>
                  <span className="text-slate-400">YoY 순이익 성장: </span>
                  <span className="text-green-400">+12.5%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}