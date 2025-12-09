import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, TrendingUp, TrendingDown, Activity, DollarSign, Building2, MapPin, Globe } from 'lucide-react';
import { Header } from './Header';
import { CompanyDetail, PriceHistoryRead } from '../types';
import { ApiError, fetchAndSaveCompany, getCompanyDetail, getPriceHistory } from '../services/api';

interface StockProfileProps {
  ticker: string;
  onBack?: () => void;
}

function getSentimentColor(score: number | null | undefined): { bg: string; text: string; barBg: string } {
  if (!score && score !== 0) return { bg: 'bg-slate-700/40', text: 'text-slate-300', barBg: 'bg-slate-700' };
  if (score >= 80) return { bg: 'bg-green-500/20', text: 'text-green-400', barBg: 'bg-green-500' };
  if (score >= 60) return { bg: 'bg-blue-500/20', text: 'text-blue-400', barBg: 'bg-blue-500' };
  if (score >= 40) return { bg: 'bg-yellow-500/20', text: 'text-yellow-400', barBg: 'bg-yellow-500' };
  return { bg: 'bg-red-500/20', text: 'text-red-400', barBg: 'bg-red-500' };
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return 'N/A';
  if (Math.abs(value) >= 1_000_000_000_000) return `${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  return value.toLocaleString();
}

export function StockProfilePage({ ticker, onBack }: StockProfileProps) {
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [prices, setPrices] = useState<PriceHistoryRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        let detail: CompanyDetail;
        try {
          detail = await getCompanyDetail(ticker);
        } catch (err) {
          const apiErr = err as ApiError;
          if (apiErr.status === 404) {
            detail = await fetchAndSaveCompany(ticker);
          } else {
            throw err;
          }
        }
        if (!mounted) return;
        setCompany(detail);

        try {
          const priceHistory = await getPriceHistory(ticker);
          if (mounted) setPrices(priceHistory);
        } catch (err) {
          const apiErr = err as ApiError;
          if (apiErr.status === 404) {
            // Attempt to collect data then retry once
            try {
              await fetchAndSaveCompany(ticker);
              const priceHistory = await getPriceHistory(ticker);
              if (mounted) setPrices(priceHistory);
            } catch (nested) {
              if (mounted) setError('가격 데이터를 불러오지 못했습니다.');
            }
          } else if (mounted) {
            setError('가격 데이터를 불러오지 못했습니다.');
          }
        }
      } catch (err) {
        if (mounted) setError((err as Error).message || '데이터를 불러오지 못했습니다.');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [ticker]);

  const latestPrice = useMemo(() => {
    if (!prices.length) return null;
    return prices[prices.length - 1];
  }, [prices]);

  const sentimentColors = getSentimentColor(company?.latest_report?.sentiment_score ?? null);

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

          {/* Loading / Error */}
          {loading && (
            <div className="flex items-center gap-2 text-slate-300">
              <div className="w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
              <span>불러오는 중...</span>
            </div>
          )}
          {error && (
            <div className="text-red-400 text-sm mb-3">
              {error}
            </div>
          )}

          {/* Company Header */}
          {company && (
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="flex items-start gap-4">
                {/* Company Logo */}
                <div className="size-16 rounded-2xl bg-white flex items-center justify-center flex-shrink-0 overflow-hidden ring-2 ring-slate-700">
                  {company.logo_url ? (
                    <img
                      src={company.logo_url}
                      alt={company.name}
                      className="size-14 object-contain"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <span className="text-slate-700 text-lg font-semibold">{company.ticker}</span>
                  )}
                </div>

                {/* Company Name & Ticker */}
                <div className="flex-1">
                  <h1 className="text-3xl text-slate-100 mb-1">
                    {company.name}
                  </h1>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm">
                      {company.ticker}
                    </span>
                  </div>

                  {/* Metadata Row */}
                  <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Building2 className="size-4" />
                      <span>{company.industry || 'N/A'}</span>
                    </div>
                    <span className="text-slate-700">•</span>
                    <div className="flex items-center gap-1.5">
                      <Activity className="size-4" />
                      <span>{company.sector || 'N/A'}</span>
                    </div>
                    <span className="text-slate-700">•</span>
                    <div className="flex items-center gap-1.5">
                      <MapPin className="size-4" />
                      <span>{company.country || 'N/A'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="flex flex-col sm:items-end gap-2">
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl text-slate-100">
                    {latestPrice?.close ? `$${latestPrice.close.toFixed(2)}` : 'N/A'}
                  </span>
                  {/* No delta info in API; placeholder */}
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <DollarSign className="size-4 text-slate-500" />
                  <span className="text-sm text-slate-400">시가총액</span>
                  <span className="text-lg text-slate-200">
                    {formatNumber(latestPrice?.market_cap)}
                  </span>
                </div>
              </div>
            </div>
          )}
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
                    {company?.latest_report?.sentiment_score ?? 'N/A'}
                  </span>
                  <span className={`px-3 py-1 ${sentimentColors.bg} ${sentimentColors.text} rounded-lg text-sm`}>
                    {company?.latest_report ? 'AI 분석' : '데이터 없음'}
                  </span>
                </div>
              </div>

              {/* Sentiment Bar */}
              <div className="relative w-full h-3 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`absolute left-0 top-0 h-full ${sentimentColors.barBg} rounded-full transition-all duration-1000 ease-out`}
                  style={{ width: `${(company?.latest_report?.sentiment_score ?? 0)}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/20"></div>
                </div>
              </div>
            </div>

            {/* Summary Content */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg text-slate-200 mb-3">종합 분석</h3>
                <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50 min-h-[120px]">
                  {company?.latest_report?.summary_content || 'AI 리포트가 없습니다.'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Price History (simple list) */}
        <div className="mb-8">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl shadow-xl overflow-hidden">
            <div className="p-6 border-b border-slate-700 flex items-center justify-between">
              <div>
                <h2 className="text-2xl text-slate-100">주가 히스토리</h2>
                <p className="text-sm text-slate-400 mt-1">최근 수집된 주가/시총</p>
              </div>
            </div>
            <div className="p-6 space-y-3">
              {prices.length === 0 ? (
                <div className="text-slate-500 text-sm">주가 데이터가 없습니다.</div>
              ) : (
                prices.slice().reverse().map((p, idx) => (
                  <div
                    key={`${p.date}-${idx}`}
                    className="flex items-center justify-between bg-slate-900/60 border border-slate-800 rounded-xl px-4 py-3"
                  >
                    <div className="text-slate-200">{p.date.split('T')[0]}</div>
                    <div className="flex items-center gap-4 text-sm text-slate-300">
                      <span>종가: ${p.close ?? 'N/A'}</span>
                      <span>시총: {formatNumber(p.market_cap)}</span>
                      <span>거래량: {p.volume ? p.volume.toLocaleString() : 'N/A'}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Financials Table */}
        <div>
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl shadow-xl overflow-hidden">
            <div className="p-6 border-b border-slate-700">
              <h2 className="text-2xl text-slate-100">재무 데이터</h2>
              <p className="text-sm text-slate-400 mt-1">연도별 주요 재무 지표</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-800/50 border-b border-slate-700">
                    <th className="px-6 py-4 text-left text-sm text-slate-300">연도</th>
                    <th className="px-6 py-4 text-right text-sm text-slate-300">매출액</th>
                    <th className="px-6 py-4 text-right text-sm text-slate-300">순이익</th>
                    <th className="px-6 py-4 text-right text-sm text-slate-300">PER</th>
                    <th className="px-6 py-4 text-right text-sm text-slate-300">시가총액</th>
                  </tr>
                </thead>
                <tbody>
                  {company?.financials?.length ? (
                    company.financials
                      .slice()
                      .sort((a, b) => b.year - a.year)
                      .map((row, index) => (
                        <tr
                          key={`${row.ticker}-${row.year}-${index}`}
                          className={`border-b border-slate-800 hover:bg-slate-800/50 transition-colors ${
                            index % 2 === 0 ? 'bg-slate-900/20' : 'bg-slate-900/40'
                          }`}
                        >
                          <td className="px-6 py-4 text-slate-200">{row.year}</td>
                          <td className="px-6 py-4 text-right text-slate-200">{formatNumber(row.revenue)}</td>
                          <td className="px-6 py-4 text-right text-slate-200">{formatNumber(row.net_income)}</td>
                          <td className="px-6 py-4 text-right text-slate-200">{row.per ?? 'N/A'}</td>
                          <td className="px-6 py-4 text-right text-slate-200">{formatNumber(row.market_cap)}</td>
                        </tr>
                      ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-6 py-4 text-center text-slate-500">
                        재무 데이터가 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}