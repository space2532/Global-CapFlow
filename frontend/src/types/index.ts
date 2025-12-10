// Auto-generated from backend Pydantic schemas (snake_case preserved)

export interface CompanyBase {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  country: string | null;
  currency: string | null;
  logo_url: string | null;
}

export interface CompanyRead extends CompanyBase {}

export interface PriceBase {
  ticker: string;
  price_date: string; // date string
  open_price: number | null;
  high_price: number | null;
  low_price: number | null;
  close_price: number | null;
  volume: number | null;
}

export interface PriceRead extends PriceBase {}

export interface FinancialRead {
  id: number | null;
  ticker: string;
  year: number;
  revenue: number | null;
  net_income: number | null;
  per: number | null;
  market_cap: number | null;
}

export interface MarketReportRead {
  summary_content: string;
  sentiment_score: number;
  collected_at: string; // datetime string
  source_type: string;
}

export interface QuarterlyReportRead {
  year: number;
  quarter: number;
  content: string | null;
  created_at: string;
}

export interface NewsSource {
  title: string;
  source: string;
  date: string;
  url: string;
}

export interface NewsItem {
  title: string;
  source: string;
  date: string;
  url: string;
  summary?: string | null;
  sources?: NewsSource[];
}

export interface CompanyDetail extends CompanyRead {
  financials: FinancialRead[];
  latest_report: MarketReportRead | null;
  latest_quarterly_report: QuarterlyReportRead | null;
  recent_news: NewsItem[];
}

export interface MatchupRequest {
  tickers: string[];
  query?: string | null;
}

export interface ComparisonPoint {
  metric: string;
  winner: string;
  reason: string;
}

export interface MatchupResponse {
  winner: string;
  reason: string;
  summary: string;
  key_comparison: ComparisonPoint[];
}

export interface RankingRead {
  year: number;
  rank: number;
  ticker: string;
  name: string;
  market_cap: number | null;
  sector: string | null;
  industry: string | null;
  logo_url: string | null;
  country: string | null;
}

export interface PriceHistoryRead {
  date: string; // datetime string
  close: number | null;
  market_cap: number | null;
  volume: number | null;
}

export interface RankHistoryItem {
  year: number;
  rank: number;
}

export interface RankHistoryRead {
  ticker: string;
  name: string;
  history: RankHistoryItem[];
}

export interface RankHistoryResponse {
  data: Record<string, RankHistoryItem[]>;
}

// Market trends / movers
export interface MarketTrend {
  date: string | null;
  dominant_sectors: { name: string; percentage: number }[];
  rising_sectors: { name: string; percentage: number }[];
  ai_analysis_text: string | null;
}

export interface MoverItem {
  rank: number | null;
  ticker: string;
  name: string;
  logo_url: string | null;
  change: number | null;
  is_new: boolean;
}

export interface RankingMovers {
  year: number | null;
  new_entries: MoverItem[];
  exited: MoverItem[];
}

