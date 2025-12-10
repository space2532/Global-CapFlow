import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Activity, DollarSign, Building2, MapPin, Globe, FileText, ExternalLink } from 'lucide-react';
import { Header } from './Header';
import { CompanyDetail, PriceHistoryRead } from '../types';
import { ApiError, fetchAndSaveCompany, getCompanyDetail, getPriceHistory } from '../services/api';

interface StockProfileProps {
  ticker: string;
  onBack?: () => void;
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return 'N/A';
  if (Math.abs(value) >= 1_000_000_000_000) return `${(value / 1_000_000_000_000).toFixed(2)}T`;
  if (Math.abs(value) >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  return value.toLocaleString();
}

function LogoWithFallback({ logoUrl, ticker, name }: { logoUrl: string | null; ticker: string; name: string }) {
  const [showFallback, setShowFallback] = useState(false);

  return (
    <div className="size-16 rounded-2xl bg-white flex items-center justify-center flex-shrink-0 overflow-hidden ring-2 ring-slate-700">
      {!showFallback && logoUrl ? (
        <img
          src={logoUrl}
          alt={name}
          className="size-14 object-contain"
          onError={() => setShowFallback(true)}
        />
      ) : (
        <span className="text-slate-700 text-lg font-semibold">{ticker}</span>
      )}
    </div>
  );
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
                <LogoWithFallback logoUrl={company.logo_url} ticker={company.ticker} name={company.name} />

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

            {/* Summary Content */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg text-slate-200 mb-3">종합 분석</h3>
                <div className="text-slate-300 leading-relaxed whitespace-pre-line bg-slate-900/40 rounded-xl p-4 border border-slate-700/50 min-h-[120px]">
                  {company?.latest_quarterly_report?.content || '리포트가 없습니다.'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 최신 뉴스 AI 요약 */}
        <div className="mb-8">
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl shadow-xl overflow-hidden">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 bg-slate-700/50 rounded-lg">
                  <FileText className="size-5 text-slate-300" />
                </div>
                <div>
                  <h2 className="text-2xl text-slate-100">최신 뉴스 AI 요약</h2>
                  <p className="text-sm text-slate-400 mt-1">AI가 분석한 주요 뉴스 및 시장 동향</p>
                </div>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {!company?.recent_news?.length ? (
                <div className="text-slate-500 text-sm">최근 뉴스가 없습니다.</div>
              ) : (
                company.recent_news.map((news, idx) => {
                  const sources = news.sources && news.sources.length > 0
                    ? news.sources
                    : [{ title: news.title, source: news.source, date: news.date, url: news.url }];

                  return (
                    <div key={`${news.url}-${idx}`} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="text-slate-100 font-semibold text-lg">{news.title || 'AI 요약'}</h3>
                          {news.summary && (
                            <p className="text-slate-300 leading-relaxed mt-2">{news.summary}</p>
                          )}
                        </div>
                        <div className="text-xs text-blue-300 bg-blue-900/30 border border-blue-700/50 rounded-full px-3 py-1">
                          출처 {sources.length}개
                        </div>
                      </div>

                      <details className="group bg-slate-800/40 rounded-lg border border-slate-800/80">
                        <summary className="flex w-full cursor-pointer items-center justify-end px-4 py-2 list-none">
                          <span className="ml-auto inline-flex items-center gap-2 text-sm text-slate-100 bg-slate-900/70 border border-slate-700 rounded-full px-3 py-1 hover:bg-slate-800 transition-colors">
                            <span className="font-medium">출처 보기</span>
                            <span className="text-slate-400 group-open:-rotate-180 transition-transform">v</span>
                          </span>
                        </summary>
                        <div className="px-4 pb-4 pt-1 space-y-3">
                          {sources.map((src, sIdx) => (
                            <div key={`${src.url}-${sIdx}`} className="rounded-md bg-slate-900/60 border border-slate-800 p-3">
                              <div className="text-slate-100 text-sm font-medium mb-1">{src.title || '제목 없음'}</div>
                              <div className="flex items-center justify-between gap-3 text-xs text-slate-400">
                                <span>{src.date || '날짜 미상'}</span>
                                <a
                                  href={src.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-blue-400 hover:text-blue-300 flex items-center gap-1.5 transition-colors"
                                >
                                  <span>출처: {src.source || '출처 미상'}</span>
                                  <ExternalLink className="size-3.5" />
                                </a>
                              </div>
                            </div>
                          ))}
                        </div>
                      </details>
                    </div>
                  );
                })
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