from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any
from datetime import datetime, timedelta, timezone
import hashlib

from .. import models, schemas
from ..database import get_db
from ..services import stock_service, news_service
from ..services.ai_service import ai_client

router = APIRouter(
    prefix="/analyze",
    tags=["analyze"],
)


def generate_request_hash(tickers: list[str], query: str | None = None) -> str:
    """
    티커들을 알파벳순으로 정렬하여 결합한 문자열로 해시를 생성합니다.
    순서가 달라도 동일한 캐시가 동작하도록 합니다.
    """
    # 티커를 대문자로 변환하고 정렬
    sorted_tickers = sorted([t.upper() for t in tickers])
    # 티커들을 언더스코어로 결합
    tickers_str = "_".join(sorted_tickers)
    # 쿼리가 있으면 포함
    if query:
        full_str = f"{tickers_str}_{query}"
    else:
        full_str = tickers_str
    # 해시 생성 (SHA256 사용)
    return hashlib.sha256(full_str.encode()).hexdigest()


async def fetch_ticker_data(ticker: str, db: AsyncSession) -> dict[str, Any]:
    """
    특정 티커의 재무 데이터와 뉴스를 DB에서 조회하거나, 없거나 오래된 경우 외부 API에서 수집합니다.
    
    - MarketReport: 최신 데이터가 24시간 이내면 DB 사용, 아니면 외부 API 호출
    - Financial: DB에서 조회, 없으면 외부 API 호출
    - Company: DB에서 조회, 없으면 외부 API 호출
    """
    ticker = ticker.upper()
    
    # 1. DB에서 최신 MarketReport 조회
    stmt = select(models.MarketReport).where(
        models.MarketReport.ticker == ticker,
        models.MarketReport.source_type == "daily_news"
    ).order_by(models.MarketReport.collected_at.desc()).limit(1)
    result = await db.execute(stmt)
    latest_report = result.scalar_one_or_none()
    
    # 2. DB에서 Financial 데이터 조회
    stmt = select(models.Financial).where(
        models.Financial.ticker == ticker
    ).order_by(models.Financial.year.desc(), models.Financial.quarter.desc())
    result = await db.execute(stmt)
    financials_db = result.scalars().all()
    
    # 3. DB에서 Company 정보 조회
    stmt = select(models.Company).where(models.Company.ticker == ticker)
    result = await db.execute(stmt)
    company_db = result.scalar_one_or_none()
    
    # 4. MarketReport가 24시간 이내인지 확인
    need_fetch_news = True
    news_data = None
    
    if latest_report:
        age_hours = (datetime.now(timezone.utc) - latest_report.collected_at).total_seconds() / 3600
        if age_hours < 24:
            # DB 데이터 사용
            need_fetch_news = False
            # raw_data를 파싱하여 news 형식으로 변환
            if latest_report.raw_data and latest_report.raw_data != "No news collected for this date":
                # raw_data에서 뉴스 정보 추출 (간단한 파싱)
                news_data = {
                    "raw_data": latest_report.raw_data,
                    "summary_content": latest_report.summary_content,
                    "sentiment_score": latest_report.sentiment_score,
                }
            else:
                news_data = {
                    "raw_data": "No news collected",
                    "summary_content": latest_report.summary_content or "No recent news available",
                    "sentiment_score": latest_report.sentiment_score or 0.0,
                }
    
    # 5. 외부 API 호출이 필요한 경우
    stock_data = None
    news_list = []
    
    if need_fetch_news or not financials_db or not company_db:
        import asyncio
        
        tasks = []
        if need_fetch_news:
            tasks.append(news_service.fetch_company_news(ticker, limit=5))
        if not financials_db or not company_db:
            tasks.append(stock_service.fetch_company_data(ticker))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        result_idx = 0
        if need_fetch_news:
            news_result = results[result_idx]
            result_idx += 1
            if not isinstance(news_result, Exception):
                news_list = news_result if isinstance(news_result, list) else []
        
        if not financials_db or not company_db:
            stock_result = results[result_idx]
            if not isinstance(stock_result, Exception):
                stock_data = stock_result
    
    # 6. 데이터 구성
    # Company 정보
    if company_db:
        company_info = {
            "ticker": company_db.ticker,
            "name": company_db.name,
            "sector": company_db.sector,
            "industry": company_db.industry,
            "currency": company_db.currency,
        }
    elif stock_data:
        company_info = stock_data.get("company", {})
    else:
        company_info = {}
    
    # Financial 데이터
    if financials_db:
        financials_list = [
            {
                "year": f.year,
                "quarter": f.quarter,
                "revenue": f.revenue,
                "net_income": f.net_income,
                "per": f.per,
                "market_cap": f.market_cap,
            }
            for f in financials_db
        ]
    elif stock_data:
        financials_list = stock_data.get("financials", [])
    else:
        financials_list = []
    
    # News 데이터 (DB에서 가져온 경우 summary_content와 raw_data 사용)
    if news_data:
        # DB에서 가져온 데이터를 news 형식으로 변환
        news_list = [news_data]
    
    return {
        "company": company_info,
        "financials": financials_list,
        "news": news_list,
    }


@router.post("/matchup", response_model=schemas.MatchupResponse, summary="기업 비교 분석 (Matchup)")
async def analyze_matchup(
    request: schemas.MatchupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    여러 기업을 비교 분석하여 승자를 선정하고 근거를 제시합니다.
    
    - tickers: 비교할 기업 티커 리스트 (예: ["AAPL", "TSLA"])
    - query: 선택적 질문 (예: "성장성 관점에서 비교해줘")
    
    동일한 티커 조합의 요청은 24시간 이내 캐시된 결과를 반환합니다.
    """
    if not request.tickers or len(request.tickers) < 2:
        raise HTTPException(
            status_code=400,
            detail="최소 2개 이상의 티커가 필요합니다."
        )
    
    # 티커 정규화 (대문자)
    tickers = [t.upper() for t in request.tickers]
    
    print(f"➡️ [AnalyzeRouter] Matchup analysis requested for {tickers}")
    
    # 1. 캐시 확인 (request_hash로 조회)
    request_hash = generate_request_hash(tickers, request.query)
    
    # 24시간 이내의 캐시 확인
    cache_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    stmt = select(models.AIAnalysis).where(
        models.AIAnalysis.request_hash == request_hash,
        models.AIAnalysis.created_at >= cache_cutoff
    ).order_by(models.AIAnalysis.created_at.desc()).limit(1)
    
    result = await db.execute(stmt)
    cached_analysis = result.scalar_one_or_none()
    
    if cached_analysis:
        print(f"✅ [AnalyzeRouter] Using cached analysis for {tickers}")
        cached_response = cached_analysis.response_json
        if isinstance(cached_response, dict):
            return schemas.MatchupResponse(**cached_response)
    
    # 2. 데이터 수집 (병렬 처리)
    print(f"📊 [AnalyzeRouter] Fetching data for {tickers}...")
    import asyncio
    
    # 모든 티커에 대해 병렬로 데이터 수집 (DB 우선, 필요시 외부 API 호출)
    ticker_tasks = [fetch_ticker_data(ticker, db) for ticker in tickers]
    ticker_data_list = await asyncio.gather(*ticker_tasks, return_exceptions=True)
    
    # 수집된 데이터를 딕셔너리로 구성
    tickers_data: dict[str, Any] = {}
    for ticker, data in zip(tickers, ticker_data_list):
        if isinstance(data, Exception):
            print(f"⚠️ Failed to fetch data for {ticker}: {data}")
            tickers_data[ticker] = {
                "company": {},
                "financials": [],
                "news": [],
            }
        else:
            tickers_data[ticker] = data
    
    # 3. AI 분석 호출
    print(f"🧠 [AnalyzeRouter] Running AI matchup analysis...")
    try:
        ai_result = await ai_client.generate_matchup_report(tickers_data)
    except Exception as e:
        print(f"❌ [AnalyzeRouter] AI analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI 분석 실패: {str(e)}"
        )
    
    # 4. 결과를 DB에 저장 (캐싱)
    try:
        # 기존 캐시가 있으면 업데이트, 없으면 생성
        if cached_analysis:
            cached_analysis.response_json = ai_result
            cached_analysis.created_at = datetime.now(timezone.utc)
        else:
            new_analysis = models.AIAnalysis(
                request_hash=request_hash,
                response_json=ai_result,
                created_at=datetime.now(timezone.utc),
            )
            db.add(new_analysis)
        
        await db.commit()
        print(f"✅ [AnalyzeRouter] Analysis result cached")
    except Exception as e:
        print(f"⚠️ [AnalyzeRouter] Failed to cache result: {e}")
        # 캐싱 실패해도 결과는 반환
        await db.rollback()
    
    # 5. 응답 반환
    return schemas.MatchupResponse(**ai_result)
