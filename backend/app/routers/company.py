from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import datetime
import re

from .. import models, schemas
from ..database import get_db
from app.services import stock_service, news_service
from app.services.ai_service import ai_client

router = APIRouter()


def parse_news_from_raw_data(raw_data: str | None, summary_content: str | None = None) -> list[schemas.NewsItem]:
    """
    raw_data 문자열에서 뉴스 아이템을 파싱합니다.
    형식: "Title: ...\nSource: ... (...)\nBody: ...\nLink: ..." 가 "\n\n---\n\n"로 구분되어 반복됩니다.
    
    Args:
        raw_data: 파싱할 원본 데이터 문자열
        summary_content: 전체 뉴스에 대한 AI 요약 (각 뉴스의 summary로 사용)
    """
    if not raw_data or raw_data == "No news collected":
        return []
    
    # 1차 파싱: 원문에서 기사 정보를 추출
    parsed_sources: list[schemas.NewsSource] = []
    news_blocks = raw_data.split("\n\n---\n\n")
    
    for block in news_blocks:
        block = block.strip()
        if not block:
            continue
        
        title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", block, re.MULTILINE)
        source_match = re.search(r"Source:\s*(.+?)\s*\((.+?)\)", block, re.MULTILINE)
        link_match = re.search(r"Link:\s*(.+?)(?:\n|$)", block, re.MULTILINE)
        
        title = title_match.group(1).strip() if title_match else ""
        source = source_match.group(1).strip() if source_match else ""
        date = source_match.group(2).strip() if source_match else ""
        url = link_match.group(1).strip() if link_match else ""
        
        if title or source or url:
            parsed_sources.append(schemas.NewsSource(
                title=title,
                source=source,
                date=date,
                url=url,
            ))
    
    if not parsed_sources:
        return []
    
    # summary_content가 있으면 동일 내용으로 간주하고 하나로 묶음
    if summary_content and summary_content.strip():
        return [
            schemas.NewsItem(
                title="AI 요약",
                source="AI 분석",
                date="",
                url="",
                summary=summary_content.strip(),
                sources=parsed_sources,
            )
        ]
    
    # summary가 없으면 제목/날짜 조합으로 중복 제거하며 묶기
    grouped_items: dict[tuple[str, str], schemas.NewsItem] = {}
    for src in parsed_sources:
        key = (src.title.lower(), src.date)
        if key not in grouped_items:
            grouped_items[key] = schemas.NewsItem(
                title=src.title,
                source=src.source,
                date=src.date,
                url=src.url,
                summary=None,
                sources=[src],
            )
        else:
            grouped_items[key].sources.append(src)
    
    return list(grouped_items.values())

@router.post("/companies/{ticker}/fetch", response_model=schemas.CompanyDetail, summary="Fetch & Save Stock + News Data")
async def fetch_company_data(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 기업의 재무 데이터(yfinance)와 최신 뉴스(DuckDuckGo)를 수집하여 DB에 저장합니다.
    저장 완료 후 CompanyDetail 객체를 반환합니다.
    """
    ticker = ticker.upper()

    print(f"➡️ [CompanyRouter] fetch_company_data called for {ticker}")

    # 1. 주식/재무 데이터 수집 (yfinance)
    try:
        stock_data = await stock_service.fetch_company_data(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock data fetch failed: {str(e)}")

    # 2. 뉴스 데이터 수집 (DuckDuckGo)
    try:
        news_list = await news_service.fetch_company_news(ticker, limit=5)
    except Exception as e:
        print(f"⚠️ News fetch failed for {ticker}: {e}")
        news_list = []  # 뉴스는 실패해도 재무 데이터는 저장 진행

    # 3. AI 분석 (뉴스와 재무 데이터 종합 분석)
    ai_result = {
        "summary": "분석 실패",
        "sentiment_score": 0.0
    }
    
    if news_list and stock_data.get("financials"):
        try:
            print(f"🧠 [CompanyRouter] Running AI analysis for {ticker}")
            # 가장 최근 재무 데이터 사용 (financials는 연도순 정렬되어 있음)
            latest_financials = stock_data["financials"][-1] if stock_data["financials"] else {}
            ai_result = await ai_client.generate_market_summary(
                ticker=ticker,
                news_list=news_list,
                financials=latest_financials
            )
        except Exception as e:
            print(f"⚠️ AI analysis failed for {ticker}: {e}")
            # AI 실패해도 기본값으로 진행

    # --- DB 저장 트랜잭션 시작 ---
    
    # 3-1. Company 정보 저장 (Upsert)
    company_info = stock_data["company"]
    # 이미 있는지 확인
    stmt = select(models.Company).where(models.Company.ticker == ticker)
    result = await db.execute(stmt)
    existing_company = result.scalar_one_or_none()

    if existing_company:
        # 정보 업데이트
        existing_company.name = company_info["name"]
        existing_company.sector = company_info["sector"]
        existing_company.industry = company_info["industry"]
        existing_company.country = company_info.get("country") or existing_company.country
        existing_company.currency = company_info["currency"]
    else:
        # 신규 생성
        new_company = models.Company(**company_info)
        db.add(new_company)
    
    # 3-2. Financials 정보 저장 (Upsert)
    for fin_item in stock_data["financials"]:
        stmt = select(models.Financial).where(
            models.Financial.ticker == ticker,
            models.Financial.year == fin_item["year"]
        )
        result = await db.execute(stmt)
        existing_fin = result.scalar_one_or_none()

        if existing_fin:
            # 업데이트
            existing_fin.revenue = fin_item["revenue"]
            existing_fin.net_income = fin_item["net_income"]
            existing_fin.per = fin_item["per"]
            existing_fin.market_cap = fin_item["market_cap"]
        else:
            # 신규 생성
            new_fin = models.Financial(**fin_item)
            db.add(new_fin)

    # 3-3. MarketReport (통합 리포트) 저장 - 종목당 1개
    if news_list or ai_result.get("summary") != "분석 실패":
        # raw_data: 수집된 뉴스 기사들의 제목/본문/링크를 합친 원문 문자열
        raw_data_parts = []
        for news in news_list:
            title = news.get("title", "")
            url = news.get("url", "")
            source = news.get("source", "")
            news_date = news.get("date", "")
            body = news.get("body", "") or news.get("snippet", "")
            raw_data_parts.append(f"Title: {title}\nSource: {source} ({news_date})\nBody: {body}\nLink: {url}")
        
        raw_data = "\n\n---\n\n".join(raw_data_parts) if raw_data_parts else "No news collected"
        
        # 중복 방지: 같은 티커, 같은 날짜의 리포트가 이미 있는지 확인
        # (collected_at이 오늘인 경우 중복으로 간주)
        today = datetime.date.today()
        stmt = select(models.MarketReport).where(
            models.MarketReport.ticker == ticker,
            models.MarketReport.source_type == "daily_update"
        ).order_by(models.MarketReport.collected_at.desc()).limit(1)
        result = await db.execute(stmt)
        existing_report = result.scalar_one_or_none()
        
        # 오늘 생성된 리포트가 있으면 업데이트, 없으면 신규 생성
        if existing_report and existing_report.collected_at.date() == today:
            # 업데이트
            existing_report.raw_data = raw_data
            existing_report.summary_content = ai_result.get("summary")
            existing_report.sentiment_score = ai_result.get("sentiment_score")
            existing_report.content = "See raw_data or summary_content"
        else:
            # 신규 생성
            report = models.MarketReport(
                ticker=ticker,
                source_type="daily_update",
                raw_data=raw_data,
                summary_content=ai_result.get("summary"),
                sentiment_score=ai_result.get("sentiment_score"),
                content="See raw_data or summary_content"
            )
            db.add(report)

    await db.commit()
    
    # 저장 완료 후 CompanyDetail 객체 구성하여 반환
    # Relationship을 활용하여 Company와 관련 데이터를 한 번에 로드
    stmt = (
        select(models.Company)
        .options(
            selectinload(models.Company.financials),
            selectinload(models.Company.market_reports)
        )
        .where(models.Company.ticker == ticker)
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=500, detail="Company not found after save")
    
    # Relationship을 통해 로드된 데이터 활용
    financials = sorted(company.financials, key=lambda f: f.year)
    
    # 최신 MarketReport 찾기 (source_type="daily_update")
    latest_report = None
    for report in sorted(company.market_reports, key=lambda r: r.collected_at, reverse=True):
        if report.source_type == "daily_update":
            latest_report = report
            break
    
    # 최신 Quarterly Report 조회 (연도/분기 내림차순 1건)
    quarterly_stmt = (
        select(models.QuarterlyReport)
        .where(models.QuarterlyReport.ticker == ticker)
        .order_by(models.QuarterlyReport.year.desc(), models.QuarterlyReport.quarter.desc())
        .limit(1)
    )
    quarterly_result = await db.execute(quarterly_stmt)
    latest_quarterly_report = quarterly_result.scalar_one_or_none()
    
    # raw_data에서 뉴스 파싱 (market_reports 테이블의 정보 활용)
    # summary_content가 없어도 뉴스는 표시 (제목, 출처는 raw_data에서 파싱)
    recent_news = []
    if latest_report and latest_report.raw_data:
        recent_news = parse_news_from_raw_data(
            latest_report.raw_data, 
            summary_content=latest_report.summary_content if latest_report.summary_content else None
        )
        print(f"📰 [CompanyRouter] Parsed {len(recent_news)} news items for {ticker}, summary_content: {bool(latest_report.summary_content)}")
    else:
        print(f"⚠️ [CompanyRouter] No market report or raw_data found for {ticker}")
    
    # CompanyDetail 객체 구성
    company_detail = schemas.CompanyDetail(
        ticker=company.ticker,
        name=company.name,
        sector=company.sector,
        industry=company.industry,
        country=company.country,
        currency=company.currency,
        logo_url=company.logo_url,
        financials=[schemas.FinancialRead.model_validate(fin) for fin in financials],
        latest_report=schemas.MarketReportRead.model_validate(latest_report) if latest_report and latest_report.summary_content else None,
        latest_quarterly_report=schemas.QuarterlyReportRead.model_validate(latest_quarterly_report) if latest_quarterly_report else None,
        recent_news=recent_news
    )
    
    return company_detail

@router.get("/companies/{ticker}", response_model=schemas.CompanyDetail)
async def get_company_detail(ticker: str, db: AsyncSession = Depends(get_db)):
    """DB에 저장된 기업 정보, 재무 데이터, 최신 AI 리포트를 조회합니다."""
    ticker = ticker.upper()
    
    # Relationship을 활용하여 Company와 관련 데이터를 한 번에 로드
    stmt = (
        select(models.Company)
        .options(
            selectinload(models.Company.financials),
            selectinload(models.Company.market_reports)
        )
        .where(models.Company.ticker == ticker)
    )
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Relationship을 통해 로드된 데이터 활용
    financials = sorted(company.financials, key=lambda f: f.year)
    
    # 최신 MarketReport 찾기 (source_type="daily_update")
    latest_report = None
    for report in sorted(company.market_reports, key=lambda r: r.collected_at, reverse=True):
        if report.source_type == "daily_update":
            latest_report = report
            break
    
    # 최신 Quarterly Report 조회 (연도/분기 내림차순 1건)
    quarterly_stmt = (
        select(models.QuarterlyReport)
        .where(models.QuarterlyReport.ticker == ticker)
        .order_by(models.QuarterlyReport.year.desc(), models.QuarterlyReport.quarter.desc())
        .limit(1)
    )
    quarterly_result = await db.execute(quarterly_stmt)
    latest_quarterly_report = quarterly_result.scalar_one_or_none()
    
    # raw_data에서 뉴스 파싱 (market_reports 테이블의 정보 활용)
    # summary_content가 없어도 뉴스는 표시 (제목, 출처는 raw_data에서 파싱)
    recent_news = []
    if latest_report and latest_report.raw_data:
        recent_news = parse_news_from_raw_data(
            latest_report.raw_data, 
            summary_content=latest_report.summary_content if latest_report.summary_content else None
        )
        print(f"📰 [CompanyRouter] Parsed {len(recent_news)} news items for {ticker}, summary_content: {bool(latest_report.summary_content)}")
    else:
        print(f"⚠️ [CompanyRouter] No market report or raw_data found for {ticker}")
    
    # CompanyDetail 객체 구성
    company_detail = schemas.CompanyDetail(
        ticker=company.ticker,
        name=company.name,
        sector=company.sector,
        industry=company.industry,
        country=company.country,
        currency=company.currency,
        logo_url=company.logo_url,
        financials=[schemas.FinancialRead.model_validate(fin) for fin in financials],
        latest_report=schemas.MarketReportRead.model_validate(latest_report) if latest_report and latest_report.summary_content else None,
        latest_quarterly_report=schemas.QuarterlyReportRead.model_validate(latest_quarterly_report) if latest_quarterly_report else None,
        recent_news=recent_news
    )
    
    return company_detail


@router.get("/companies/{ticker}/prices", response_model=List[schemas.PriceHistoryRead], summary="특정 기업의 주가 및 시가총액 히스토리")
async def get_company_prices(
    ticker: str,
    limit: Optional[int] = Query(default=None, ge=1, description="반환할 최근 데이터 수 (선택, 전체 조회 시 생략)"),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 기업의 주가 및 시가총액 히스토리를 반환합니다 (Line Chart 용).
    
    - ticker: 기업 티커
    - limit: 반환할 최근 데이터 수 (선택, 생략 시 전체 조회)
    - 날짜 오름차순 정렬
    """
    ticker = ticker.upper()
    
    # Company 존재 확인
    stmt = select(models.Company).where(models.Company.ticker == ticker)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Price 히스토리 조회 (날짜 오름차순)
    stmt = (
        select(models.Price)
        .where(models.Price.ticker == ticker)
        .order_by(models.Price.date)
    )
    
    # limit이 지정된 경우 최근 N개만 조회 (날짜 내림차순으로 limit 후 다시 오름차순 정렬)
    if limit is not None:
        # 서브쿼리로 최근 N개 날짜를 먼저 찾고, 그 데이터를 오름차순으로 정렬
        stmt = stmt.order_by(models.Price.date.desc()).limit(limit)
        result = await db.execute(stmt)
        prices = result.scalars().all()
        # 날짜 오름차순으로 다시 정렬
        prices = sorted(prices, key=lambda p: p.date)
    else:
        result = await db.execute(stmt)
        prices = result.scalars().all()
    
    if not prices:
        raise HTTPException(
            status_code=404,
            detail=f"No price history found for ticker {ticker}"
        )
    
    # PriceHistoryRead 스키마로 변환
    price_history = [
        schemas.PriceHistoryRead(
            date=price.date,
            close=price.close,
            market_cap=price.market_cap,
            volume=price.volume
        )
        for price in prices
    ]
    
    return price_history