from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import datetime
import traceback

from .. import models, schemas
from ..database import get_db
from ..services import stock_service, news_service
from ..services.ai_service import ai_client

router = APIRouter()

@router.post("/companies/{ticker}/fetch", summary="Fetch & Save Stock + News Data")
async def fetch_company_data(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 기업의 재무 데이터(yfinance)와 최신 뉴스(DuckDuckGo)를 수집하여 DB에 저장합니다.
    """
    try:
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
            # raw_data: 수집된 뉴스 기사들의 제목/링크를 합친 원문 문자열
            raw_data_parts = []
            for news in news_list:
                title = news.get("title", "")
                url = news.get("url", "")
                source = news.get("source", "")
                news_date = news.get("date", "")
                raw_data_parts.append(f"Title: {title}\nSource: {source} ({news_date})\nLink: {url}")
            
            raw_data = "\n\n---\n\n".join(raw_data_parts) if raw_data_parts else "No news collected"
            
            # 중복 방지: 같은 티커, 같은 날짜의 리포트가 이미 있는지 확인
            # (collected_at이 오늘인 경우 중복으로 간주)
            today = datetime.date.today()
            stmt = select(models.MarketReport).where(
                models.MarketReport.ticker == ticker,
                models.MarketReport.source_type == "daily_update"
            ).order_by(models.MarketReport.collected_at.desc())
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
        
        return {
            "status": "success", 
            "ticker": ticker, 
            "financials_count": len(stock_data["financials"]),
            "news_count": len(news_list),
            "ai_summary": ai_result.get("summary"),
            "sentiment_score": ai_result.get("sentiment_score")
        }
    except Exception as e:
        print(f"❌ Critical Error in fetch_company_data:\n{traceback.format_exc()}")
        return {
            "status": "error",
            "detail": str(e),
            "trace": traceback.format_exc()
        }

@router.get("/companies/{ticker}", response_model=schemas.CompanyRead)
async def get_company_detail(ticker: str, db: AsyncSession = Depends(get_db)):
    """DB에 저장된 기업 정보를 조회합니다."""
    stmt = select(models.Company).where(models.Company.ticker == ticker.upper())
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    return company