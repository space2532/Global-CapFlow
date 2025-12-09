from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class CompanyBase(BaseModel):
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    country: str | None = None
    currency: str | None = None
    logo_url: str | None = None

    model_config = {"from_attributes": True}


class CompanyRead(CompanyBase):
    pass


class PriceBase(BaseModel):
    ticker: str
    price_date: date
    open_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    close_price: Decimal | None = None
    volume: int | None = None

    model_config = {"from_attributes": True}


class PriceRead(PriceBase):
    pass


class FinancialRead(BaseModel):
    id: int | None = None
    ticker: str
    year: int
    revenue: float | None = None
    net_income: float | None = None
    per: float | None = None
    market_cap: float | None = None

    model_config = {"from_attributes": True}


class MarketReportRead(BaseModel):
    summary_content: str
    sentiment_score: float
    collected_at: datetime
    source_type: str

    model_config = {"from_attributes": True}


class CompanyDetail(CompanyRead):
    financials: list[FinancialRead] = []
    latest_report: MarketReportRead | None = None


class MatchupRequest(BaseModel):
    """기업 비교 분석 요청 스키마"""
    tickers: list[str]
    query: str | None = None


class ComparisonPoint(BaseModel):
    """비교 포인트 항목"""
    metric: str
    winner: str
    reason: str


class MatchupResponse(BaseModel):
    """기업 비교 분석 응답 스키마"""
    winner: str
    reason: str
    summary: str
    key_comparison: list[ComparisonPoint]


class RankingRead(BaseModel):
    """순위 정보 조회용 스키마 - models.Ranking과 models.Company의 정보를 합친 형태"""
    year: int
    rank: int
    ticker: str
    name: str
    market_cap: float | None = None
    sector: str | None = None
    industry: str | None = None

    model_config = {"from_attributes": True}


class PriceHistoryRead(BaseModel):
    """차트용 시계열 데이터 스키마"""
    date: datetime
    close: float | None = None
    market_cap: float | None = None
    volume: int | None = None

    model_config = {"from_attributes": True}


class RankHistoryItem(BaseModel):
    """연도별 순위 항목"""
    year: int
    rank: int

    model_config = {"from_attributes": True}


class RankHistoryRead(BaseModel):
    """특정 기업의 연도별 순위 변동 내역 (Bump Chart용)"""
    ticker: str
    name: str
    history: list[RankHistoryItem]

    model_config = {"from_attributes": True}


class RankHistoryResponse(BaseModel):
    """순위 히스토리 응답 스키마 (티커별 그룹화)"""
    data: dict[str, list[RankHistoryItem]]


