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


