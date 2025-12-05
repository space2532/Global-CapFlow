# from __future__ import annotations 제거: SQLModel Relationship이 타입 힌트를 올바르게 파싱하도록 함
from datetime import date as dt_date, datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Column, Text, UniqueConstraint, Date, DateTime
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    # 순환 참조 방지를 위한 타입 체크 전용 import
    pass


class Company(SQLModel, table=True):
    """기본 종목 마스터."""

    __tablename__ = "companies"

    ticker: str = Field(primary_key=True, index=True, max_length=32)
    name: str = Field(index=True, max_length=255)
    category: str = Field(default="Stock", max_length=32, description="Stock, Meme, Product 등 분류")
    sector: Optional[str] = Field(default=None, max_length=128)
    industry: Optional[str] = Field(default=None, max_length=128)
    country: Optional[str] = Field(default=None, max_length=128)
    currency: Optional[str] = Field(default=None, max_length=32)

    # Relationship 복구: from __future__ import annotations 제거로 타입 힌트가 즉시 평가되어 SQLModel이 관계를 올바르게 파싱
    financials: List["Financial"] = Relationship(back_populates="company", sa_relationship_kwargs={"lazy": "selectin"})
    market_reports: List["MarketReport"] = Relationship(back_populates="company", sa_relationship_kwargs={"lazy": "selectin"})
    prices: List["Price"] = Relationship(back_populates="company", sa_relationship_kwargs={"lazy": "selectin"})
    rankings: List["Ranking"] = Relationship(back_populates="company", sa_relationship_kwargs={"lazy": "selectin"})


class Financial(SQLModel, table=True):
    """연도/분기별 재무 지표."""

    __tablename__ = "financials"
    __table_args__ = (
        UniqueConstraint("ticker", "year", "quarter", name="uq_financials_ticker_year_quarter"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(
        foreign_key="companies.ticker",
        index=True,
    )
    year: int = Field(index=True)
    quarter: Optional[int] = Field(
        default=None,
        description="1~4분기, 0 또는 NULL이면 연간 데이터",
    )
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    per: Optional[float] = None
    market_cap: Optional[float] = None

    company: Optional["Company"] = Relationship(back_populates="financials", sa_relationship_kwargs={"lazy": "selectin"})


class Price(SQLModel, table=True):
    """월별 주가 및 시가총액."""

    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_prices_ticker_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(
        foreign_key="companies.ticker",
        index=True,
    )
    date: datetime = Field(
        description="해당 월의 기준일 (예: 월말)",
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    close: Optional[float] = Field(default=None, description="종가")
    market_cap: Optional[float] = Field(default=None, description="시가총액")
    volume: Optional[int] = Field(default=None, description="거래량")

    company: Optional["Company"] = Relationship(back_populates="prices", sa_relationship_kwargs={"lazy": "selectin"})


class Ranking(SQLModel, table=True):
    """연/월별 시가총액 순위."""

    __tablename__ = "rankings"
    # 월별 관리로 전환: 기존 (year, rank) → (ranking_date, rank) 유니크로 변경
    __table_args__ = (
        UniqueConstraint("ranking_date", "rank", name="uq_rankings_ranking_date_rank"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True)
    ranking_date: Optional[dt_date] = Field(
        default=None,
        sa_column=Column(Date, nullable=True, index=True),
        description="순위 산정 기준일 (월말 등). 기존 연도 데이터 호환을 위해 nullable.",
    )
    rank: int = Field(index=True, description="해당 연도 내 시가총액 순위 (1위부터)")
    ticker: str = Field(
        foreign_key="companies.ticker",
        index=True,
        description="순위 기준이 된 종목 티커",
    )
    market_cap: Optional[float] = Field(default=None, description="해당 연도 기준 시가총액")
    company_name: str = Field(max_length=255, description="당시 사명 (이력 보존용)")

    company: Optional["Company"] = Relationship(back_populates="rankings", sa_relationship_kwargs={"lazy": "selectin"})


class SectorTrend(SQLModel, table=True):
    """월별 산업 트렌드 분석 결과."""

    __tablename__ = "sector_trends"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt_date = Field(
        sa_column=Column(Date, nullable=False, index=True),
        description="분석 기준일 (월말 등)",
    )
    dominant_sectors: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="상위 섹터 통계",
    )
    rising_sectors: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="급상승 섹터",
    )
    new_entries: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="신규 진입 기업 목록",
    )
    ai_analysis_text: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="AI가 작성한 트렌드 분석",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class MarketReport(SQLModel, table=True):
    """뉴스/리포트 등 마켓 리포트 텍스트."""

    __tablename__ = "market_reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(
        foreign_key="companies.ticker",
        index=True,
    )
    # 핵심 데이터: AI가 요약한 텍스트
    summary_content: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True), description="AI가 요약한 텍스트")
    # 감성 분석 점수
    sentiment_score: Optional[float] = Field(default=None, description="긍정/부정 지수 -1.0 ~ 1.0")
    # 임시 저장용 원문 (Pruning 전까지 보관)
    raw_data: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True), description="임시 저장용 원문")
    # 기존 content 필드 (하위 호환성 유지, raw_data와 동일한 역할)
    content: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    source_type: str = Field(max_length=32)
    report_period: Optional[str] = Field(
        default=None,
        max_length=32,
        description='보고서 기간 식별용 (예: "2024-Q1").',
    )

    company: Optional["Company"] = Relationship(back_populates="market_reports", sa_relationship_kwargs={"lazy": "selectin"})


class QuarterlyReport(SQLModel, table=True):
    """분기별 기업 분석 리포트."""

    __tablename__ = "quarterly_reports"
    __table_args__ = (
        UniqueConstraint("ticker", "year", "quarter", name="uq_quarterly_reports_ticker_year_quarter"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(
        foreign_key="companies.ticker",
        index=True,
    )
    year: int = Field(index=True)
    quarter: int = Field(index=True, description="1~4 분기")
    content: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="분기별 종합 분석 텍스트",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class AIAnalysis(SQLModel, table=True):
    """AI 분석 캐시 테이블."""

    __tablename__ = "ai_analysis"

    id: Optional[int] = Field(default=None, primary_key=True)
    # 동일한 질문 캐싱용 해시
    request_hash: str = Field(index=True, unique=True, max_length=255)

    # 응답 JSON (PostgreSQL JSONB로 매핑, 다른 DB에서는 일반 JSON/Text로 동작)
    response_json: dict | list | str = Field(
        sa_column=Column(JSON, nullable=False)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
