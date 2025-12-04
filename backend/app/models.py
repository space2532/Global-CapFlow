from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


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

    # 관계는 SQLAlchemy 2.0+ 호환성 문제로 인해 일시적으로 주석 처리
    # 필요시 나중에 추가 가능
    # financials: List["Financial"] = Relationship(back_populates="company")
    # market_reports: List["MarketReport"] = Relationship(back_populates="company")


class Financial(SQLModel, table=True):
    """연도별 재무 지표."""

    __tablename__ = "financials"
    __table_args__ = (
        UniqueConstraint("ticker", "year", name="uq_financials_ticker_year"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(
        foreign_key="companies.ticker",
        index=True,
    )
    year: int = Field(index=True)
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    per: Optional[float] = None
    market_cap: Optional[float] = None

    # company: Optional[Company] = Relationship(back_populates="financials")


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
    collected_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    source_type: str = Field(max_length=32)

    # company: Optional[Company] = Relationship(back_populates="market_reports")


class AIAnalysis(SQLModel, table=True):
    """AI 분석 캐시 테이블."""

    __tablename__ = "ai_analysis"

    id: Optional[int] = Field(default=None, primary_key=True)
    # 동일한 질문 캐싱용 해시
    request_hash: str = Field(index=True, unique=True, max_length=255)

    # 응답 JSON (PostgreSQL JSONB로 매핑, 다른 DB에서는 일반 JSON/Text로 동작)
    response_json: dict | list | str = Field(
        sa_column=Column(JSONB, nullable=False)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
