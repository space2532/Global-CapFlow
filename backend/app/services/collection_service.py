import asyncio
import io
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import requests
import yfinance as yf
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from . import news_service, stock_service
from .ai_service import ai_client


WIKI_INDEX_SOURCES: List[Dict[str, Any]] = [
    {
        "name": "S&P 500 (US)",
        "url": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "suffix": "",
    },
    {
        "name": "Nasdaq 100 (US)",
        "url": "https://en.wikipedia.org/wiki/Nasdaq-100",
        "suffix": "",
    },
    {
        "name": "FTSE 100 (UK)",
        "url": "https://en.wikipedia.org/wiki/FTSE_100_Index",
        "suffix": ".L",  # 런던 상장 종목 (런던거래소)
    },
    {
        "name": "DAX 40 (Germany)",
        "url": "https://en.wikipedia.org/wiki/DAX",
        "suffix": ".DE",
    },
    {
        "name": "CAC 40 (France)",
        "url": "https://en.wikipedia.org/wiki/CAC_40",
        "suffix": ".PA",
    },
    {
        "name": "Nikkei 225 (Japan)",
        "url": "https://en.wikipedia.org/wiki/Nikkei_225",
        "suffix": ".T",
    },
    {
        "name": "Hang Seng Index (Hong Kong)",
        "url": "https://en.wikipedia.org/wiki/Hang_Seng_Index",
        "suffix": ".HK",
    },
]

def _extract_tickers_from_tables(
    tables: List[pd.DataFrame],
    ticker_suffix: str = "",
) -> List[str]:
    """HTML 테이블 목록에서 티커(symbol) 컬럼을 찾아 리스트로 추출."""

    # 블랙리스트 키워드: 일반 단어나 회사 유형 키워드가 티커로 잘못 인식되는 것을 방지
    IGNORE_KEYWORDS = {
        "WEBSITE", "CLOSING", "GLOBAL", "EUROPE", "OTHER", "ENERGY", "METALS",
        "WATER", "MAJOR", "CANADA", "INDIA", "OCEANIA", "BRAZIL", "AFRICA",
        "MEXICO", "JAPAN", "FRANCE", "DATE", "ADDED", "REMOVED", "COMPONENT",
        "INDUSTRY", "SECTOR", "SUBSECTOR", "PERU", "CHILE", "BANKS", "MEDIA",
        "REUTERS", "TYPE", "HISTORY", "WALES", "ENGLAND", "SCOTLAND", "IRELAND",
        "NORTHERN", "SECTORS", "INDICES", "POLICY", "ASIA", "AMERICAS",
        "CONSTITUENTS", "COMPONENTS", "FTSE", "DAX", "CAC", "NIKKEI", "HANG",
        "SENG", "TOPIX", "NOTES", "REFERENCES", "EXTERNAL", "LINKS", "SEE",
        "ALSO", "MOVERS", "RISING", "FALLING", "CHANGE", "PERCENT", "VOLUME",
        "PRICE", "HIGH", "LOW", "UK", "US", "GERMANY", "HONG", "KONG",
        # 요구사항에 따른 추가 키워드
        "MARKET", "MARKETS", "FINANCE", "CHINA", "WORLD", "INTERNATIONAL", 
        "GROUP", "HOLDINGS", "CORP", "CORPORATION", "LIMITED", "LTD", "PLC", 
        "INC", "NV", "SA", "AG", "SE", "SAPA", "IPA"
    }

    possible_symbol_columns = {
        "symbol",
        "ticker",
        "ticker symbol",
        "code",
        "epic",
    }

    tickers: List[str] = []

    for df in tables:
        # 컬럼 이름을 소문자로 매핑
        lower_cols = {str(c).strip().lower(): c for c in df.columns}
        symbol_col: Optional[str] = None

        for key in possible_symbol_columns:
            if key in lower_cols:
                symbol_col = lower_cols[key]
                break

        if symbol_col is None:
            if len(df.columns) > 0:
                symbol_col = df.columns[0]
            else:
                continue

        for raw in df[symbol_col].dropna().astype(str).tolist():
            ticker = raw.strip()
            
            # 1. 길이가 1글자 미만이면 제외
            if len(ticker) < 1:
                continue
            
            # 2. 공백이나 콤마가 있으면 제외
            if " " in ticker or "," in ticker:
                continue
            
            # 3. 콜론(:)이 포함되어 있으면 제외
            if ":" in ticker:
                continue
            
            # 4. 순수 심볼 추출 (점 이전 부분만)
            pure_symbol = ticker.split(".")[0] if "." in ticker else ticker
            
            # 5. 미국 시장(suffix가 없는 경우)의 숫자 티커 차단
            # 미국 티커는 알파벳만 사용하므로, 숫자로만 구성된 티커는 무조건 제외
            if not ticker_suffix and pure_symbol.isdigit():
                continue
            
            # 6. 연도/날짜 필터링 강화: 순수 심볼이 4자리 숫자이고 19xx 또는 20xx로 시작하면 제외
            if pure_symbol.isdigit() and len(pure_symbol) == 4:
                if pure_symbol.startswith("19") or pure_symbol.startswith("20"):
                    continue
            
            # 7. 블랙리스트 검사 (대문자 변환)
            ticker_upper = ticker.upper()
            pure_upper = pure_symbol.upper()
            
            if ticker_upper in IGNORE_KEYWORDS or pure_upper in IGNORE_KEYWORDS:
                continue
            
            if "DATE" in ticker_upper or "TIME" in ticker_upper:
                continue

            # 8. 길이 제한 강화: 숫자가 아닌 티커의 경우 순수 심볼 길이가 6글자를 초과하면 제외
            # 단, 숫자로 된 티커(홍콩, 일본 등)는 허용
            if not pure_symbol.isdigit() and len(pure_symbol) > 6:
                continue

            # 9. 숫자로만 구성된 경우 추가 검증
            if pure_symbol.isdigit():
                # 접미사 없는 긴 숫자는 이상함 (5자 이상)
                if len(pure_symbol) >= 5 and not ticker_suffix:
                    continue

            # 10. 접미사 부여 로직 개선: 이미 점(.)이 포함되어 있으면 접미사를 붙이지 않음
            # 예: AIR.PA에는 .DE를 붙이지 않음
            if ticker_suffix:
                # 이미 접미사가 붙어있으면 스킵
                if ticker.endswith(ticker_suffix):
                    pass  # 이미 올바른 접미사가 있음
                # 점(.)이 이미 포함되어 있으면 접미사를 붙이지 않음
                elif "." in ticker:
                    pass  # 이미 다른 접미사가 있으므로 중복 방지
                else:
                    # 점이 없을 때만 접미사 추가
                    ticker = f"{ticker}{ticker_suffix}"

            # 11. 최종 검증: 점이 2개 이상이 되었는지 확인 (중복 접미사 방지)
            if ticker.count(".") >= 2:
                continue

            tickers.append(ticker.upper())

    # 중복 제거, 순서 유지
    seen: Set[str] = set()
    unique_tickers: List[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique_tickers.append(t)
    return unique_tickers


async def fetch_index_tickers() -> List[str]:
    """
    위키피디아 + pandas.read_html 로 주요 글로벌 지수 구성 종목 티커를 수집합니다.

    대상:
    - S&P 500 (미국)
    - Nasdaq 100 (미국)
    - FTSE 100 (영국)
    - DAX 40 (독일)
    - CAC 40 (프랑스)
    - Nikkei 225 (일본)
    - Hang Seng Index (홍콩)
    """

    def _sync_job() -> List[str]:
        headers = {
            # 위키피디아 등에서 봇 차단을 피하기 위한 일반적인 브라우저 UA
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        all_tickers: List[str] = []

        # 1) 각 지수의 위키피디아 페이지에서 테이블 파싱
        for item in WIKI_INDEX_SOURCES:
            url = item["url"]
            suffix = item.get("suffix", "")

            try:
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
            except Exception:
                # 개별 지수 페이지가 실패해도 나머지는 계속 시도
                continue

            try:
                tables = pd.read_html(io.StringIO(resp.text))
            except ValueError:
                # 테이블이 없으면 패스
                continue

            all_tickers.extend(
                _extract_tickers_from_tables(tables, ticker_suffix=suffix)
            )

        # 2) 전체 지수에서 중복 제거
        seen: Set[str] = set()
        unique_tickers: List[str] = []
        for t in all_tickers:
            if t not in seen:
                seen.add(t)
                unique_tickers.append(t)

        # 3) 네트워크 문제 등으로 위키 수집이 모두 실패한 경우,
        #    최소한 파이프라인을 테스트할 수 있도록 대표 글로벌 대형주 티커로 Fallback.
        if not unique_tickers:
            unique_tickers = [
                "AAPL",
                "MSFT",
                "GOOGL",
                "GOOG",
                "AMZN",
                "NVDA",
                "META",
                "TSLA",
                "BRK-B",
                "LLY",
                "JPM",
                "V",
                "WMT",
                "MA",
                "XOM",
            ]

        return unique_tickers

    return await asyncio.to_thread(_sync_job)


async def _fetch_single_ticker_yf(ticker: str) -> Optional[Dict[str, Any]]:
    """yfinance로 단일 티커의 시가총액 / 가격 / 회사 정보 조회."""

    def _sync_job() -> Optional[Dict[str, Any]]:
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}
        except Exception:
            info = {}

        market_cap = info.get("marketCap")
        price = info.get("currentPrice") or info.get("regularMarketPrice")

        if market_cap is None and price is None:
            # yfinance에서 의미있는 데이터를 얻지 못한 경우
            return None

        data: Dict[str, Any] = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "currency": info.get("currency"),
            "market_cap": float(market_cap) if market_cap is not None else None,
            "price": float(price) if price is not None else None,
            "volume": info.get("volume"),
        }

        # TODO: currency != USD 인 경우, 별도 FX 레이트를 조회하여 USD 기준으로 변환하는 로직을 추가할 수 있습니다.
        data["market_cap_usd"] = data["market_cap"]

        # --- FMP Fallback (예시 스켈레톤, 실제 호출은 선택 사항) ---
        # if data["market_cap"] is None or data["price"] is None:
        #     try:
        #         api_key = "YOUR_FMP_API_KEY"
        #         url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={api_key}"
        #         resp = requests.get(url, timeout=10)
        #         resp.raise_for_status()
        #         items = resp.json()
        #         if items:
        #             item = items[0]
        #             data["price"] = data["price"] or item.get("price")
        #             data["market_cap"] = data["market_cap"] or item.get("marketCap")
        #             data["market_cap_usd"] = data["market_cap"]
        #     except Exception:
        #         pass

        return data

    return await asyncio.to_thread(_sync_job)


async def fetch_top_100_data(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    수집된 티커 목록에 대해 yfinance를 사용하여 시가총액 / 가격을 조회하고,
    시가총액(USD 기준) 상위 100개를 반환합니다.
    """

    # 비동기적으로 병렬 조회
    tasks = [asyncio.create_task(_fetch_single_ticker_yf(t)) for t in tickers]
    results = await asyncio.gather(*tasks)

    # None 제거 및 시가총액 없는 항목 제거
    valid_items: List[Dict[str, Any]] = [
        r for r in results
        if r is not None and r.get("market_cap_usd") is not None
    ]

    # 시가총액 기준 내림차순 정렬
    valid_items.sort(key=lambda x: x["market_cap_usd"] or 0.0, reverse=True)

    # 상위 100개 선택
    return valid_items[:100]


async def update_rankings_db(
    top_100_list: List[Dict[str, Any]],
    db: AsyncSession,
) -> None:
    """
    상위 100개 기업 정보를 DB에 저장/업데이트합니다.

    - companies: 존재하지 않으면 생성 (insert), 있으면 그대로 두거나 일부 필드 업데이트
    - rankings: year=현재년도 기준으로 순위 정보 upsert (간단히 기존 연도 데이터 삭제 후 재삽입)
    - prices: 당일 기준 가격/시가총액 저장 (티커+날짜 unique 기준 upsert)
    """

    if not top_100_list:
        return

    current_year = datetime.now(timezone.utc).year
    today = datetime.now(timezone.utc).date()
    price_date = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    # 1) Company upsert (배치로 기존 티커 조회 후, 없는 것만 insert)
    tickers = [item["ticker"] for item in top_100_list]

    stmt = select(models.Company).where(models.Company.ticker.in_(tickers))
    result = await db.execute(stmt)
    existing_companies = {c.ticker: c for c in result.scalars().all()}

    for item in top_100_list:
        ticker = item["ticker"]
        if ticker in existing_companies:
            company = existing_companies[ticker]
            # 기본 정보는 최신 데이터로 업데이트
            company.name = item.get("name") or company.name
            company.sector = item.get("sector") or company.sector
            company.industry = item.get("industry") or company.industry
            company.currency = item.get("currency") or company.currency
        else:
            company = models.Company(
                ticker=ticker,
                name=item.get("name") or ticker,
                sector=item.get("sector"),
                industry=item.get("industry"),
                currency=item.get("currency"),
            )
            db.add(company)

    # 2) Rankings: 해당 연도 데이터 전체 삭제 후, 1~100위 재삽입
    await db.execute(
        delete(models.Ranking).where(models.Ranking.year == current_year)
    )

    for rank, item in enumerate(top_100_list, start=1):
        ranking = models.Ranking(
            year=current_year,
            rank=rank,
            ticker=item["ticker"],
            market_cap=item.get("market_cap_usd"),
            company_name=item.get("name") or item["ticker"],
        )
        db.add(ranking)

    # 3) Prices: (ticker, date) 기준 upsert
    for item in top_100_list:
        ticker = item["ticker"]

        stmt = select(models.Price).where(
            models.Price.ticker == ticker,
            models.Price.date == price_date,
        )
        result = await db.execute(stmt)
        existing_price = result.scalar_one_or_none()

        if existing_price:
            existing_price.close = item.get("price")
            existing_price.market_cap = item.get("market_cap_usd")
            existing_price.volume = item.get("volume")
        else:
            price = models.Price(
                ticker=ticker,
                date=price_date,
                close=item.get("price"),
                market_cap=item.get("market_cap_usd"),
                volume=item.get("volume"),
            )
            db.add(price)

    await db.commit()


async def _calculate_ranking_changes(
    db: AsyncSession,
    current_top_100: List[Dict[str, Any]],
    ranking_date: date,
) -> Dict[str, Any]:
    """
    이번 랭킹과 가장 최근의 과거 랭킹을 비교해 변동 데이터를 생성합니다.
    """
    current_tickers: Set[str] = {item["ticker"] for item in current_top_100}

    # 섹터별 통계 집계 (값이 없으면 Unknown으로 분류)
    sector_stats: Dict[str, int] = {}
    for item in current_top_100:
        sector = item.get("sector") or "Unknown"
        sector_stats[sector] = sector_stats.get(sector, 0) + 1

    # 1) ranking_date 기준 직전 데이터 날짜 조회
    latest_past_date_stmt = (
        select(models.Ranking.ranking_date)
        .where(models.Ranking.ranking_date.is_not(None))
        .where(models.Ranking.ranking_date < ranking_date)
        .order_by(models.Ranking.ranking_date.desc())
        .limit(1)
    )
    result = await db.execute(latest_past_date_stmt)
    latest_past_date = result.scalar_one_or_none()

    previous_tickers: Set[str] = set()

    if latest_past_date:
        prev_stmt = select(models.Ranking.ticker).where(
            models.Ranking.ranking_date == latest_past_date
        )
        prev_result = await db.execute(prev_stmt)
        previous_tickers = set(prev_result.scalars().all())
    else:
        # ranking_date가 없는 기존 연/월 데이터 호환용: 직전 연도의 랭킹을 사용
        fallback_year_stmt = (
            select(models.Ranking.year)
            .where(models.Ranking.year < ranking_date.year)
            .order_by(models.Ranking.year.desc())
            .limit(1)
        )
        fallback_year_result = await db.execute(fallback_year_stmt)
        fallback_year = fallback_year_result.scalar_one_or_none()

        if fallback_year is not None:
            prev_stmt = select(models.Ranking.ticker).where(
                models.Ranking.year == fallback_year
            )
            prev_result = await db.execute(prev_stmt)
            previous_tickers = set(prev_result.scalars().all())

    new_entries = sorted(current_tickers - previous_tickers)
    exited = sorted(previous_tickers - current_tickers)

    return {
        "previous_ranking_date": latest_past_date,
        "new_entries": new_entries,
        "exited": exited,
        "sector_stats": sector_stats,
    }


async def collect_and_update_global_top_100(db: AsyncSession) -> Dict[str, Any]:
    """
    엔드투엔드 파이프라인:
    - 주요 지수 구성 종목 티커 수집
    - yfinance로 시가총액 상위 100개 선정
    - DB에 companies / rankings 업데이트 (과거 데이터 보존)
    - 변동 데이터 계산 후 함께 반환
    """
    tickers = await fetch_index_tickers()
    top_100 = await fetch_top_100_data(tickers)
    ranking_date = datetime.now(timezone.utc).date()
    
    # 변동 데이터 계산 (기존 데이터는 유지)
    changes = await _calculate_ranking_changes(db, top_100, ranking_date)

    # Rankings만 업데이트 (년별 상위 100개 기업 재조사)
    current_year = ranking_date.year
    tickers_list = [item["ticker"] for item in top_100]
    
    # Company 정보 업데이트
    stmt = select(models.Company).where(models.Company.ticker.in_(tickers_list))
    result = await db.execute(stmt)
    existing_companies = {c.ticker: c for c in result.scalars().all()}
    
    for item in top_100:
        ticker = item["ticker"]
        if ticker in existing_companies:
            company = existing_companies[ticker]
            company.name = item.get("name") or company.name
            company.sector = item.get("sector") or company.sector
            company.industry = item.get("industry") or company.industry
            company.currency = item.get("currency") or company.currency
        else:
            company = models.Company(
                ticker=ticker,
                name=item.get("name") or ticker,
                sector=item.get("sector"),
                industry=item.get("industry"),
                currency=item.get("currency"),
            )
            db.add(company)

    # Rankings: 기존 데이터 삭제 (재실행 시 중복 방지)
    await db.execute(delete(models.Ranking).where(models.Ranking.ranking_date == ranking_date))

    # Rankings: 오늘 날짜(ranking_date)로 신규 삽입
    for rank, item in enumerate(top_100, start=1):
        ranking = models.Ranking(
            year=current_year,
            ranking_date=ranking_date,
            rank=rank,
            ticker=item["ticker"],
            market_cap=item.get("market_cap_usd"),
            company_name=item.get("name") or item["ticker"],
        )
        db.add(ranking)
    
    await db.commit()
    return {
        "top_100": top_100,
        "ranking_date": ranking_date,
        "changes": changes,
    }


async def _process_single_ticker_news(
    ticker: str,
) -> tuple[str, dict | None, bool]:
    """
    단일 티커의 뉴스 수집 및 처리 (병렬 처리용)
    DB 세션은 사용하지 않고 데이터만 수집하여 반환.
    
    Returns:
        (ticker, report_data, success)
    """
    try:
        # 뉴스와 재무 데이터를 병렬로 수집
        news_task = news_service.fetch_company_news(ticker, limit=5)
        stock_task = stock_service.fetch_company_data(ticker)
        
        news_list, stock_data = await asyncio.gather(
            news_task,
            stock_task,
            return_exceptions=True
        )
        
        # 뉴스 수집 실패 여부 확인
        news_failed = isinstance(news_list, Exception)
        
        # 예외 처리
        if isinstance(news_list, Exception):
            news_list = []
        if isinstance(stock_data, Exception):
            stock_data = {"financials": []}
        
        # 뉴스가 없거나 실패한 경우 DB 저장 건너뛰기
        if news_failed or not news_list or len(news_list) == 0:
            return (ticker, None, False)
        
        # AI 분석 (뉴스가 있을 때만)
        ai_result = {
            "summary": "No recent news available",
            "sentiment_score": 0.0
        }
        
        if news_list and stock_data.get("financials"):
            try:
                financials_list = stock_data["financials"]
                latest_financial = financials_list[-1] if financials_list else {}
                
                ai_result = await ai_client.generate_market_summary(
                    ticker=ticker,
                    financials=latest_financial,
                    news_list=news_list,
                )
            except Exception:
                # AI 분석 실패해도 뉴스는 저장
                pass
        
        # raw_data 구성 (뉴스가 있는 경우만)
        raw_data_parts = []
        for news in news_list:
            title = news.get("title", "")
            url = news.get("url", "")
            source = news.get("source", "")
            news_date = news.get("date", "")
            raw_data_parts.append(f"Title: {title}\nSource: {source} ({news_date})\nLink: {url}")
        raw_data = "\n\n---\n\n".join(raw_data_parts)
        
        return (ticker, {
            "raw_data": raw_data,
            "summary_content": ai_result.get("summary"),
            "sentiment_score": ai_result.get("sentiment_score"),
        }, True)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"뉴스 수집 실패 ({ticker}): {type(e).__name__}: {e}")
        return (ticker, None, False)


async def collect_news_for_top_100(db: AsyncSession) -> int:
    """
    상위 100개 기업의 뉴스를 수집하여 MarketReport에 저장합니다. (일별 실행)
    배치 병렬 처리로 성능 최적화.
    
    Returns:
        수집한 기업 수
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 현재 상위 100개 기업 조회
    current_year = datetime.now(timezone.utc).year
    stmt = select(models.Ranking).where(
        models.Ranking.year == current_year
    ).order_by(models.Ranking.rank).limit(100)
    result = await db.execute(stmt)
    rankings = result.scalars().all()
    
    if not rankings:
        return 0
    
    tickers = [r.ticker for r in rankings]
    today_utc = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today_utc, datetime.min.time()).replace(tzinfo=timezone.utc)
    today_end = datetime.combine(today_utc, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    logger.info(f"뉴스 수집 시작: {len(tickers)}개 기업")
    
    # 배치 크기 설정 (동시에 처리할 기업 수) - TPM 한도 고려하여 5로 설정
    BATCH_SIZE = 5
    collected_count = 0
    failed_count = 0
    
    # 배치 단위로 처리
    for batch_start in range(0, len(tickers), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(tickers))
        batch_tickers = tickers[batch_start:batch_end]
        
        logger.info(f"배치 처리: {batch_start + 1}~{batch_end}/{len(tickers)}")
        
        # 배치 내에서 병렬 처리 (DB 세션 없이 데이터만 수집)
        tasks = [
            _process_single_ticker_news(ticker)
            for ticker in batch_tickers
        ]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과를 DB에 저장 (순차적으로)
        for result in batch_results:
            if isinstance(result, Exception):
                failed_count += 1
                continue
            
            ticker, report_data, success = result
            
            if not success or report_data is None:
                failed_count += 1
                continue
            
            try:
                # 기존 리포트 확인
                stmt = select(models.MarketReport).where(
                    models.MarketReport.ticker == ticker,
                    models.MarketReport.source_type == "daily_news",
                    models.MarketReport.collected_at >= today_start,
                    models.MarketReport.collected_at <= today_end
                ).order_by(models.MarketReport.collected_at.desc()).limit(1)
                result = await db.execute(stmt)
                existing_report = result.scalar_one_or_none()
                
                if existing_report:
                    # 업데이트
                    existing_report.raw_data = report_data["raw_data"]
                    existing_report.summary_content = report_data["summary_content"]
                    existing_report.sentiment_score = report_data["sentiment_score"]
                    existing_report.content = "See raw_data or summary_content"
                else:
                    # 신규 생성
                    report = models.MarketReport(
                        ticker=ticker,
                        source_type="daily_news",
                        raw_data=report_data["raw_data"],
                        summary_content=report_data["summary_content"],
                        sentiment_score=report_data["sentiment_score"],
                        content="See raw_data or summary_content",
                        collected_at=datetime.now(timezone.utc)
                    )
                    db.add(report)
                
                collected_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"DB 저장 실패 ({ticker}): {e}")
                continue
        
        # 배치마다 커밋 (진행 상황 저장)
        try:
            await db.commit()
        except Exception as e:
            logger.error(f"배치 커밋 실패: {e}")
            await db.rollback()
        
        # 마지막 배치가 아닌 경우에만 API 호출 제한 방지를 위한 딜레이 (TPM 한도 고려)
        if batch_end < len(tickers):
            logger.info(f"API 호출 제한 방지를 위해 10초 대기...")
            await asyncio.sleep(10)
    
    if failed_count > 0:
        logger.warning(f"수집 완료: 성공 {collected_count}개, 실패 {failed_count}개")
    else:
        logger.info(f"수집 완료: {collected_count}개 기업")
    
    return collected_count
    
    await db.commit()
    return collected_count


async def collect_daily_prices(db: AsyncSession) -> int:
    """
    상위 100개 기업의 일별 주가·시가총액·거래량을 수집하여 Price 테이블에 저장합니다. (일별 실행)
    
    Returns:
        수집한 기업 수
    """
    # 현재 상위 100개 기업 조회
    current_year = datetime.now(timezone.utc).year
    stmt = select(models.Ranking).where(
        models.Ranking.year == current_year
    ).order_by(models.Ranking.rank).limit(100)
    result = await db.execute(stmt)
    rankings = result.scalars().all()
    
    if not rankings:
        return 0
    
    tickers = [r.ticker for r in rankings]
    
    # 오늘 날짜 계산
    now = datetime.now(timezone.utc)
    today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    
    collected_count = 0
    
    # 병렬로 데이터 수집
    tasks = [asyncio.create_task(_fetch_single_ticker_yf(t)) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception) or result is None:
            continue
        
        try:
            stmt = select(models.Price).where(
                models.Price.ticker == ticker,
                models.Price.date == today,
            )
            db_result = await db.execute(stmt)
            existing_price = db_result.scalar_one_or_none()
            
            if existing_price:
                existing_price.close = result.get("price")
                existing_price.market_cap = result.get("market_cap_usd")
                existing_price.volume = result.get("volume")
            else:
                price = models.Price(
                    ticker=ticker,
                    date=today,
                    close=result.get("price"),
                    market_cap=result.get("market_cap_usd"),
                    volume=result.get("volume"),
                )
                db.add(price)
            
            collected_count += 1
            
        except Exception:
            continue
    
    await db.commit()
    return collected_count


async def collect_quarterly_financials(db: AsyncSession) -> int:
    """
    상위 100개 기업의 분기별 재무 데이터를 수집하여 Financial 테이블에 저장합니다. (분기별 실행)
    
    Returns:
        수집한 기업 수
    """
    # 현재 상위 100개 기업 조회
    current_year = datetime.now(timezone.utc).year
    stmt = select(models.Ranking).where(
        models.Ranking.year == current_year
    ).order_by(models.Ranking.rank).limit(100)
    result = await db.execute(stmt)
    rankings = result.scalars().all()
    
    if not rankings:
        return 0
    
    tickers = [r.ticker for r in rankings]
    collected_count = 0
    
    # 현재 분기 계산 (1~4)
    now = datetime.now(timezone.utc)
    current_quarter = (now.month - 1) // 3 + 1
    
    for ticker in tickers:
        try:
            stock_data = await stock_service.fetch_company_data(ticker)
            
            if not stock_data.get("financials"):
                continue
            
            # 최신 재무 데이터를 현재 분기로 저장
            latest_financial = stock_data["financials"][-1] if stock_data["financials"] else None
            
            if latest_financial:
                stmt = select(models.Financial).where(
                    models.Financial.ticker == ticker,
                    models.Financial.year == latest_financial["year"],
                    models.Financial.quarter == current_quarter
                )
                result = await db.execute(stmt)
                existing_fin = result.scalar_one_or_none()
                
                if existing_fin:
                    existing_fin.revenue = latest_financial.get("revenue")
                    existing_fin.net_income = latest_financial.get("net_income")
                    existing_fin.per = latest_financial.get("per")
                    existing_fin.market_cap = latest_financial.get("market_cap")
                else:
                    financial = models.Financial(
                        ticker=ticker,
                        year=latest_financial["year"],
                        quarter=current_quarter,
                        revenue=latest_financial.get("revenue"),
                        net_income=latest_financial.get("net_income"),
                        per=latest_financial.get("per"),
                        market_cap=latest_financial.get("market_cap"),
                    )
                    db.add(financial)
                
                collected_count += 1
                
        except Exception:
            continue
    
    await db.commit()
    return collected_count


