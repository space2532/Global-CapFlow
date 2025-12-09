import asyncio
import io
from datetime import datetime, date, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from io import StringIO

import pandas as pd
import requests
import yfinance as yf
from bs4 import BeautifulSoup
from requests_cache import CachedSession
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.config import settings
from app.services import news_service, stock_service
from app.services.ai_service import ai_client

# 환율 캐시 (통화 → USD 환산율)
EXCHANGE_RATE_CACHE: Dict[str, float] = {}

# 국가별 야후 파이낸스 티커 접미사 맵
COUNTRY_SUFFIX_MAP = {
    "United Kingdom": ".L",
    "Japan": ".T",
    "China": ".SS",  # 기본값은 상해, 숫자 규칙은 별도 처리
    "Germany": ".DE",
    "France": ".PA",
    "Hong Kong": ".HK",
    "Canada": ".TO",
    "Australia": ".AX",
    "Taiwan": ".TW",
    "South Korea": ".KS",
    "India": ".NS",
}


def _apply_country_suffix(ticker: str, country: Optional[str]) -> str:
    """
    국가 정보를 기반으로 티커에 접미사를 자동 부착합니다.
    - 이미 '.'을 포함하면 그대로 반환
    - 중국: 6자리 숫자 티커일 때 6/9 시작 -> .SS, 0/3 시작 -> .SZ
    - 그 외 COUNTRY_SUFFIX_MAP에 존재하면 해당 접미사 부착
    """
    if not ticker:
        return ticker
    ticker = ticker.upper()

    # 이미 접미사가 있는 경우 그대로 반환
    if "." in ticker:
        return ticker

    if country == "China":
        if ticker.isdigit() and len(ticker) == 6:
            if ticker.startswith(("0", "3")):
                return f"{ticker}.SZ"
            if ticker.startswith(("6", "9")):
                return f"{ticker}.SS"
        # 규칙에 맞지 않으면 기본 접미사 적용
        suffix = COUNTRY_SUFFIX_MAP.get(country)
        return f"{ticker}{suffix}" if suffix else ticker

    suffix = COUNTRY_SUFFIX_MAP.get(country or "")
    return f"{ticker}{suffix}" if suffix else ticker


async def get_usd_exchange_rate(currency: Optional[str]) -> float:
    """
    주어진 통화 1단위가 USD로 얼마인지 환율을 반환합니다.
    - USD는 1.0
    - 캐시 사용
    - yfinance 심볼:
        1) USD{currency}=X → last_price가 1 USD당 현지통화이므로 역수 사용
        2) {currency}USD=X → last_price 그대로 사용
    - 모두 실패 시 1.0 반환
    """
    if not currency:
        return 1.0

    currency = currency.upper()
    if currency == "USD":
        return 1.0

    if currency in EXCHANGE_RATE_CACHE:
        return EXCHANGE_RATE_CACHE[currency]

    def _fetch_rate_sync() -> float:
        # 케이스 1: USD{currency}=X (예: USDJPY=X) → 1 / last_price
        try:
            pair = f"USD{currency}=X"
            ticker = yf.Ticker(pair)
            last_price = None
            if ticker.fast_info and ticker.fast_info.last_price is not None:
                last_price = float(ticker.fast_info.last_price)
            elif ticker.info:
                last_price = ticker.info.get("regularMarketPrice") or ticker.info.get("lastPrice")
            if last_price:
                return 1.0 / float(last_price)
        except Exception:
            pass

        # 케이스 2: {currency}USD=X (예: EURUSD=X) → last_price
        try:
            pair = f"{currency}USD=X"
            ticker = yf.Ticker(pair)
            last_price = None
            if ticker.fast_info and ticker.fast_info.last_price is not None:
                last_price = float(ticker.fast_info.last_price)
            elif ticker.info:
                last_price = ticker.info.get("regularMarketPrice") or ticker.info.get("lastPrice")
            if last_price:
                return float(last_price)
        except Exception:
            pass

        # 실패 시 fallback
        return 1.0

    rate = await asyncio.to_thread(_fetch_rate_sync)
    EXCHANGE_RATE_CACHE[currency] = rate
    return rate

# 위키피디아 요청용 캐시 세션 (24시간 TTL - 위키피디아 데이터는 자주 변경되지 않음)
_wiki_cache_session: Optional[CachedSession] = None


def _get_wiki_session() -> requests.Session:
    """
    위키피디아 요청용 캐시된 세션을 반환합니다.
    중복 호출을 방지하여 Rate Limit을 피합니다.
    """
    global _wiki_cache_session
    if _wiki_cache_session is None:
        _wiki_cache_session = CachedSession(
            cache_name='wikipedia_cache',
            backend='sqlite',
            expire_after=86400,  # 24시간
            cache_control=True,
        )
        _wiki_cache_session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
    return _wiki_cache_session


_fmp_session: Optional[requests.Session] = None


def _get_fmp_session() -> requests.Session:
    """
    FMP 이미지 요청용 세션을 반환합니다.
    Keep-Alive를 활용해 연결 오버헤드를 줄입니다.
    """
    global _fmp_session
    if _fmp_session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,*/*;q=0.8",
            "Connection": "keep-alive",
        })
        _fmp_session = session
    return _fmp_session


def _search_japanese_ticker(company_name: str) -> Optional[str]:
    """
    회사 이름을 기반으로 일본 주식 티커(.T로 끝나는)를 검색합니다.
    Yahoo Finance Search API를 사용하여 검색하고, .T로 끝나는 티커를 반환합니다.
    
    Args:
        company_name: 회사 이름 (예: "Toyota Motor Corporation")
        
    Returns:
        일본 주식 티커 (예: "7203.T") 또는 None
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 회사 이름 정제 (괄호, 특수 문자 제거)
        clean_name = company_name.split('(')[0].strip()
        if not clean_name:
            return None
        
        # Yahoo Finance Search API 사용
        # yfinance는 직접 검색 기능이 없으므로, Yahoo Finance의 검색 API를 직접 호출
        search_url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": clean_name}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        resp = requests.get(search_url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        quotes = data.get("quotes", [])
        if not quotes:
            return None
        
        # .T로 끝나는 티커 찾기 (일본 주식)
        japanese_tickers = [
            quote.get("symbol") 
            for quote in quotes 
            if quote.get("symbol", "").endswith(".T")
        ]
        
        if not japanese_tickers:
            return None
        
        # 여러 개가 있으면 첫 번째 것 선택
        # (일반적으로 가장 관련성 높은 결과가 첫 번째에 옴)
        selected_ticker = japanese_tickers[0]
        
        # ADR이 아닌 일반 주식을 선호 (ADR은 보통 ".TO" 등 다른 suffix를 가짐)
        # .T로 끝나는 것은 일반적으로 일본 주식이므로 그대로 사용
        return selected_ticker
        
    except Exception as e:
        logger.debug(f"티커 검색 실패 ({company_name}): {e}")
        return None


def _verify_ticker_with_yfinance(ticker: str) -> bool:
    """
    yfinance를 사용하여 티커가 유효한지 확인합니다.
    HTTP 404 등의 에러 발생 시 False를 반환합니다.
    """
    try:
        t = yf.Ticker(ticker)
        # fast_info를 먼저 확인 (속도 최적화)
        if t.fast_info and t.fast_info.last_price is not None:
            return True
        
        # fast_info가 안될 경우 info 확인
        info = t.info
        if info and (info.get("marketCap") or info.get("currentPrice") or info.get("regularMarketPrice")):
            return True
            
        return False
    except Exception:
        return False


def _parse_nikkei_225(html_content: str, logger) -> tuple[List[str], List[str]]:
    """
    Nikkei 225 Wikipedia 페이지에서 종목 티커를 파싱합니다.
    구조: <div class="mw-heading2"><h2>Components</h2></div> -> ... -> <h3>Sector</h3> -> <ul> -> <li>
    """
    import re
    from bs4 import BeautifulSoup, Tag
    
    resolved_tickers = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Components 헤더 찾기
        header = soup.find(id="Components")
        if not header:
            # id로 못 찾으면 텍스트로 시도
            for h2 in soup.find_all('h2'):
                if "components" in h2.get_text().lower():
                    header = h2
                    break
        
        if not header:
            logger.warning("   ⚠️ Nikkei 'Components' 헤더를 찾을 수 없습니다.")
            return [], []

        # 🚨 [핵심 수정] 위키피디아의 최신 구조 대응 (Vector 2022 skin)
        # <h2>가 <div class="mw-heading ..."> 안에 갇혀 있는 경우, 부모 div로 올라감
        start_node = header
        if header.parent and header.parent.name == 'div' and 'mw-heading' in header.parent.get('class', []):
            start_node = header.parent
            
        logger.info(f"   ℹ️ Nikkei 파싱 시작 노드: {start_node.name} (class: {start_node.get('class')})")

        # 2. 다음 메인 섹션(H2)이 나올 때까지 형제 노드 순회
        # Components 섹션 아래에는 여러 개의 <h3>(섹터)와 <ul>(종목 리스트)이 섞여 있음
        for sibling in start_node.next_siblings:
            # Tag 객체가 아닌 경우(공백 문자열 등) 건너뜀
            if not isinstance(sibling, Tag):
                continue

            # 다음 메인 섹션 헤더(H2)를 만나면 종료
            # 1) <h2> 태그인 경우
            if sibling.name == 'h2':
                break
            # 2) <div class="mw-heading mw-heading2"> 안에 <h2>가 있는 경우
            if sibling.name == 'div' and 'mw-heading2' in sibling.get('class', []):
                break
                
            # 리스트(ul)를 만나면 파싱
            if sibling.name == 'ul':
                for li in sibling.find_all('li'):
                    text = li.get_text().strip() # 예: "ANA Holdings Inc. (TYO: 9202)"
                    
                    # 정규식: (TYO: 9202) 패턴 찾기
                    # 이미지에 따르면 괄호 안에 TYO: 숫자 패턴이 있음
                    match = re.search(r'TYO:\s*(\d{4})', text, re.IGNORECASE)
                    if match:
                        code = match.group(1)
                        ticker = f"{code}.T"
                        resolved_tickers.append(ticker)
                    else:
                        # 예비 패턴: 괄호 안에 4자리 숫자만 있는 경우
                        alt_match = re.search(r'\((\d{4})\)', text)
                        if alt_match:
                            code = alt_match.group(1)
                            ticker = f"{code}.T"
                            resolved_tickers.append(ticker)

    except Exception as e:
        logger.error(f"   ❌ Nikkei 225 파싱 오류: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return [], []

    # 중복 제거
    unique_tickers = sorted(list(set(resolved_tickers)))
    
    if unique_tickers:
        logger.info(f"   ✅ {len(unique_tickers)}개 Nikkei 티커 추출 완료")
    else:
        logger.warning("   ⚠️ Nikkei 티커 추출 실패 (0개)")

    return unique_tickers, []


def _parse_hang_seng_index(html_content: str, logger) -> tuple[List[str], List[str]]:
    """
    Hang Seng Index: 숫자 티커를 4자리로 패딩(zfill)하여 .HK 붙임
    """
    import re
    try:
        html_io = StringIO(html_content)
        tables = pd.read_html(html_io)
        resolved_tickers = []
        unresolved_companies = []
        
        for table in tables:
            if isinstance(table.columns, pd.MultiIndex):
                table.columns = table.columns.get_level_values(0)
            
            ticker_column = next((col for col in table.columns if 'ticker' in str(col).lower() or 'symbol' in str(col).lower() or 'code' in str(col).lower()), None)
            
            if ticker_column is None:
                continue
            
            for _, row in table.iterrows():
                try:
                    ticker_raw = str(row[ticker_column]).strip()
                    if not ticker_raw or ticker_raw.lower() == 'nan':
                        continue
                    
                    # 숫자만 추출
                    digits = re.sub(r'\D', '', ticker_raw)
                    
                    if digits and len(digits) <= 5:
                        ticker = f"{digits.zfill(4)}.HK"
                        if _verify_ticker_with_yfinance(ticker):
                            resolved_tickers.append(ticker)
                        else:
                            unresolved_companies.append(ticker)
                    elif _verify_ticker_with_yfinance(ticker_raw):
                        resolved_tickers.append(ticker_raw)
                            
                except Exception:
                    continue
                    
        return list(set(resolved_tickers)), unresolved_companies
    except Exception as e:
        logger.error(f"   ❌ Hang Seng 파싱 오류: {e}")
        return [], []


def _search_hong_kong_ticker(company_name: str) -> Optional[str]:
    """
    회사 이름을 기반으로 홍콩 주식 티커(.HK로 끝나는)를 검색합니다.
    
    Args:
        company_name: 회사 이름
        
    Returns:
        홍콩 주식 티커 (예: "0700.HK") 또는 None
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        clean_name = company_name.split('(')[0].strip()
        if not clean_name:
            return None
        
        # Yahoo Finance Search API 사용
        search_url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": clean_name}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        resp = requests.get(search_url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        quotes = data.get("quotes", [])
        if not quotes:
            return None
        
        # .HK로 끝나는 티커 찾기
        hk_tickers = [
            quote.get("symbol") 
            for quote in quotes 
            if quote.get("symbol", "").endswith(".HK")
        ]
        
        if not hk_tickers:
            return None
        
        return hk_tickers[0]
        
    except Exception as e:
        logger.debug(f"홍콩 티커 검색 실패 ({company_name}): {e}")
        return None


def _parse_csi_300_index(html_content: str, logger) -> tuple[List[str], List[str]]:
    """
    CSI 300: "SSE: 600519" 같은 텍스트에서 숫자만 추출하여 .SS/.SZ 매핑
    """
    import re
    try:
        html_io = StringIO(html_content)
        tables = pd.read_html(html_io)
        resolved_tickers = []
        unresolved_companies = []
        
        for table in tables:
            if isinstance(table.columns, pd.MultiIndex):
                table.columns = table.columns.get_level_values(0)
            
            ticker_column = next((col for col in table.columns if 'ticker' in str(col).lower() or 'symbol' in str(col).lower() or 'code' in str(col).lower()), None)
            
            if ticker_column is None:
                continue
            
            for _, row in table.iterrows():
                try:
                    raw_val = str(row[ticker_column])
                    match = re.search(r'(\d{6})', raw_val)
                    if not match:
                        continue
                    
                    ticker_digits = match.group(1)
                    
                    # 상해(SS) vs 심천(SZ) 구분
                    if ticker_digits.startswith('6') or ticker_digits.startswith('9'):
                        suffix = '.SS'
                    else:
                        suffix = '.SZ'
                    
                    ticker = f"{ticker_digits}{suffix}"
                    
                    if _verify_ticker_with_yfinance(ticker):
                        resolved_tickers.append(ticker)
                    else:
                        # 실패 시 반대 거래소 시도
                        alt_suffix = '.SZ' if suffix == '.SS' else '.SS'
                        alt_ticker = f"{ticker_digits}{alt_suffix}"
                        if _verify_ticker_with_yfinance(alt_ticker):
                            resolved_tickers.append(alt_ticker)
                                
                except Exception:
                    continue

        logger.info(f"   ✅ {len(resolved_tickers)}개 CSI 300 티커 추출 완료")
        return list(set(resolved_tickers)), []
    except Exception as e:
        logger.error(f"   ❌ CSI 300 파싱 오류: {e}")
        return [], []


def _search_china_ticker(company_name: str) -> Optional[str]:
    """
    회사 이름을 기반으로 중국 주식 티커(.SS 또는 .SZ로 끝나는)를 검색합니다.
    
    Args:
        company_name: 회사 이름
        
    Returns:
        중국 주식 티커 (예: "600519.SS" 또는 "000001.SZ") 또는 None
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        clean_name = company_name.split('(')[0].strip()
        if not clean_name:
            return None
        
        # Yahoo Finance Search API 사용
        search_url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {"q": clean_name}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        resp = requests.get(search_url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        quotes = data.get("quotes", [])
        if not quotes:
            return None
        
        # .SS 또는 .SZ로 끝나는 티커 찾기
        china_tickers = [
            quote.get("symbol") 
            for quote in quotes 
            if quote.get("symbol", "").endswith((".SS", ".SZ"))
        ]
        
        if not china_tickers:
            return None
        
        return china_tickers[0]
        
    except Exception as e:
        logger.debug(f"중국 티커 검색 실패 ({company_name}): {e}")
        return None


def _parse_dax(html_content: str, logger) -> tuple[List[str], List[str]]:
    """
    DAX Wikipedia 페이지에서 .DE로 끝나는 티커를 찾아 추출합니다.
    헤더 이름 대신 데이터 패턴(Content-based)을 사용하여 테이블을 찾습니다.
    """
    try:
        html_io = StringIO(html_content)
        # 헤더를 특정하지 않고 데이터를 모두 읽음
        tables = pd.read_html(html_io, header=None)
        
        resolved_tickers = []
        unresolved_companies = []  # DAX는 보통 티커가 명확하므로 빈 리스트 사용
        
        found_table = False
        
        for table in tables:
            # 테이블의 각 컬럼을 순회하며 .DE 패턴 검사
            for col_idx in table.columns:
                # 상위 10개 행만 샘플링하여 패턴 확인
                sample_values = table[col_idx].astype(str).head(10).tolist()
                
                # ".DE"로 끝나는 데이터가 절반 이상이면 티커 컬럼으로 간주
                de_matches = [v for v in sample_values if v.strip().endswith('.DE')]
                
                if len(de_matches) >= 3:  # 최소 3개 이상 매칭되면 확신
                    found_table = True
                    # 해당 컬럼 전체 데이터 추출
                    tickers = table[col_idx].astype(str).tolist()
                    for ticker in tickers:
                        clean_ticker = ticker.strip()
                        if clean_ticker.endswith('.DE'):
                            resolved_tickers.append(clean_ticker)
                    break  # 컬럼 찾음 -> 테이블 루프 종료
            
            if found_table:
                break  # 테이블 찾음 -> 전체 루프 종료
                
        if resolved_tickers:
            logger.info(f"   ✅ {len(resolved_tickers)}개 DAX 티커 추출 완료 (패턴 매칭)")
            return list(set(resolved_tickers)), []
        else:
            logger.warning("   ⚠️  DAX 테이블을 찾지 못했습니다 (.DE 패턴 없음)")
            return [], []
            
    except Exception as e:
        logger.error(f"   ❌ DAX 파싱 오류: {e}")
        return [], []


# 주요 지수 위키피디아 페이지 URL 목록
WIKI_INDEX_SOURCES = [
    {
        "url": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        "suffix": "",
        "country": "United States",
    },
    # 수집량 감소 요청에 따라 NASDAQ-100 임시 비활성화
    # {
    #     "url": "https://en.wikipedia.org/wiki/NASDAQ-100",
    #     "suffix": "",
    #     "country": "United States",
    # },
    {
        "url": "https://en.wikipedia.org/wiki/CAC_40",
        "suffix": "",
        "country": "France",
    },
    {
        "url": "https://en.wikipedia.org/wiki/FTSE_100_Index",
        "suffix": "",
        "country": "United Kingdom",
    },
    {
        "url": "https://en.wikipedia.org/wiki/DAX",
        "suffix": "",
        "special_handling": "dax",  # DAX는 특별 처리 필요
        "country": "Germany",
    },
    # {
    #     "url": "https://en.wikipedia.org/wiki/Nikkei_225",
    #     "suffix": "",
    #     "special_handling": "nikkei_225",  # Nikkei 225는 특별 처리 필요
    #     "country": "Japan",
    # },
    {
        "url": "https://en.wikipedia.org/wiki/Hang_Seng_Index",
        "suffix": "",
        "special_handling": "hang_seng",  # Hang Seng Index는 특별 처리 필요
        "country": "Hong Kong",
    },
    # {
    #     "url": "https://en.wikipedia.org/wiki/CSI_300_Index",
    #     "suffix": "",
    #     "special_handling": "csi_300",  # CSI 300 Index는 특별 처리 필요
    #     "country": "China",
    # },
]

# 특별 처리 대상 URL 상수
NIKKEI_225_URL = "https://en.wikipedia.org/wiki/Nikkei_225"
HANG_SENG_URL = "https://en.wikipedia.org/wiki/Hang_Seng_Index"
CSI_300_URL = "https://en.wikipedia.org/wiki/CSI_300_Index"


async def fetch_index_tickers() -> Dict[str, str]:
    """
    주요 지수(예: S&P 500, NASDAQ-100 등)의 위키피디아 페이지에서 구성 종목 티커를 수집합니다.
    위키피디아 테이블을 파싱하여 티커 심볼을 추출합니다.
    
    Returns:
        {ticker: country} 형태의 딕셔너리
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("📋 [Step 1] 티커 수집 시작: 위키피디아에서 주요 지수 구성 종목 수집 중...")
    logger.info(f"   대상 지수: {len(WIKI_INDEX_SOURCES)}개")
    for idx, item in enumerate(WIKI_INDEX_SOURCES, 1):
        logger.info(f"   {idx}. {item['url']}")
    
    def _sync_job() -> tuple[Dict[str, str], dict]:
        import logging
        sync_logger = logging.getLogger(__name__)
        
        # 캐시된 세션 사용 (중복 호출 방지)
        session = _get_wiki_session()
        
        # 2) 위키피디아 HTML에서 테이블 파싱 (pandas.read_html 사용)
        all_tickers_map: Dict[str, str] = {}
        success_count = 0
        fail_count = 0
        error_details = []
        
        for item in WIKI_INDEX_SOURCES:
            url = item["url"]
            suffix = item.get("suffix", "")
            special_handling = item.get("special_handling", "")
            country = item.get("country", "Unknown")
            is_nikkei_225 = special_handling == "nikkei_225" or url == NIKKEI_225_URL
            is_hang_seng = special_handling == "hang_seng" or url == HANG_SENG_URL
            is_csi_300 = special_handling == "csi_300" or url == CSI_300_URL
            is_dax = special_handling == "dax" or url == "https://en.wikipedia.org/wiki/DAX"
            
            try:
                # 위키피디아는 User-Agent가 없으면 403 Forbidden을 반환합니다
                # requests로 HTML을 가져온 후 pandas.read_html에 전달
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                # requests로 HTML 가져오기
                resp = session.get(url, headers=headers, timeout=30)
                resp.raise_for_status()
                html_content = resp.text
                
                # Nikkei 225 특별 처리
                if is_nikkei_225:
                    sync_logger.info(f"🇯🇵 [Nikkei 225] 특별 처리 시작: Components 섹션에서 종목 파싱 중...")
                    
                    try:
                        resolved_tickers, unresolved_companies = _parse_nikkei_225(html_content, sync_logger)
                        
                        # 해결된 티커 추가
                        for ticker in resolved_tickers:
                            all_tickers_map[ticker] = country
                        
                        tickers_from_this_source = len(resolved_tickers)
                        
                        if tickers_from_this_source > 0:
                            success_count += 1
                            error_details.append(
                                f"✅ {url}: {tickers_from_this_source}개 티커 해결"
                                + (f", {len(unresolved_companies)}개 미해결" if unresolved_companies else "")
                            )
                        else:
                            fail_count += 1
                            error_details.append(
                                f"⚠️  {url}: 티커 해결 실패"
                                + (f" ({len(unresolved_companies)}개 종목)" if unresolved_companies else "")
                            )
                    except Exception as e:
                        fail_count += 1
                        import traceback
                        error_msg = f"❌ {url}: Nikkei 225 파싱 오류 - {type(e).__name__}: {str(e)[:200]}"
                        error_details.append(error_msg)
                        sync_logger.error(f"   {error_msg}")
                    
                    continue  # Nikkei 225 처리 완료, 다음 URL로
                
                # Hang Seng Index 특별 처리
                if is_hang_seng:
                    sync_logger.info(f"🇭🇰 [Hang Seng Index] 특별 처리 시작: 티커 정규화 중...")
                    
                    try:
                        resolved_tickers, unresolved_companies = _parse_hang_seng_index(html_content, sync_logger)
                        
                        # 해결된 티커 추가
                        for ticker in resolved_tickers:
                            all_tickers_map[ticker] = country
                        
                        tickers_from_this_source = len(resolved_tickers)
                        
                        if tickers_from_this_source > 0:
                            success_count += 1
                            error_details.append(
                                f"✅ {url}: {tickers_from_this_source}개 티커 해결"
                                + (f", {len(unresolved_companies)}개 미해결" if unresolved_companies else "")
                            )
                        else:
                            fail_count += 1
                            error_details.append(
                                f"⚠️  {url}: 티커 해결 실패"
                                + (f" ({len(unresolved_companies)}개 종목)" if unresolved_companies else "")
                            )
                    except Exception as e:
                        fail_count += 1
                        import traceback
                        error_msg = f"❌ {url}: Hang Seng Index 파싱 오류 - {type(e).__name__}: {str(e)[:200]}"
                        error_details.append(error_msg)
                        sync_logger.error(f"   {error_msg}")
                    
                    continue  # Hang Seng Index 처리 완료, 다음 URL로
                
                # CSI 300 Index 특별 처리
                if is_csi_300:
                    sync_logger.info(f"🇨🇳 [CSI 300 Index] 특별 처리 시작: 티커 정규화 중...")
                    
                    try:
                        resolved_tickers, unresolved_companies = _parse_csi_300_index(html_content, sync_logger)
                        
                        # 해결된 티커 추가
                        for ticker in resolved_tickers:
                            all_tickers_map[ticker] = country
                        
                        tickers_from_this_source = len(resolved_tickers)
                        
                        if tickers_from_this_source > 0:
                            success_count += 1
                            error_details.append(
                                f"✅ {url}: {tickers_from_this_source}개 티커 해결"
                                + (f", {len(unresolved_companies)}개 미해결" if unresolved_companies else "")
                            )
                        else:
                            fail_count += 1
                            error_details.append(
                                f"⚠️  {url}: 티커 해결 실패"
                                + (f" ({len(unresolved_companies)}개 종목)" if unresolved_companies else "")
                            )
                    except Exception as e:
                        fail_count += 1
                        import traceback
                        error_msg = f"❌ {url}: CSI 300 Index 파싱 오류 - {type(e).__name__}: {str(e)[:200]}"
                        error_details.append(error_msg)
                        sync_logger.error(f"   {error_msg}")
                    
                    continue  # CSI 300 Index 처리 완료, 다음 URL로
                
                # DAX 특별 처리
                if is_dax:
                    sync_logger.info(f"🇩🇪 [DAX] 특별 처리 시작: .DE 패턴 매칭 중...")
                    
                    try:
                        resolved_tickers, unresolved_companies = _parse_dax(html_content, sync_logger)
                        
                        # 해결된 티커 추가
                        for ticker in resolved_tickers:
                            all_tickers_map[ticker] = country
                        
                        tickers_from_this_source = len(resolved_tickers)
                        
                        if tickers_from_this_source > 0:
                            success_count += 1
                            error_details.append(
                                f"✅ {url}: {tickers_from_this_source}개 티커 해결"
                                + (f", {len(unresolved_companies)}개 미해결" if unresolved_companies else "")
                            )
                        else:
                            fail_count += 1
                            error_details.append(
                                f"⚠️  {url}: 티커 해결 실패"
                                + (f" ({len(unresolved_companies)}개 종목)" if unresolved_companies else "")
                            )
                    except Exception as e:
                        fail_count += 1
                        import traceback
                        error_msg = f"❌ {url}: DAX 파싱 오류 - {type(e).__name__}: {str(e)[:200]}"
                        error_details.append(error_msg)
                        sync_logger.error(f"   {error_msg}")
                    
                    continue  # DAX 처리 완료, 다음 URL로
                
                # 일반 지수 처리 (기존 로직)
                # pandas.read_html로 HTML 파싱
                # 여러 파서 시도 (lxml → html5lib → 기본)
                tables = None
                parser_used = None
                last_error = None
                
                for parser_name in ['lxml', 'html5lib', None]:
                    try:
                        # StringIO로 감싸서 FutureWarning 해결
                        html_io = StringIO(html_content)
                        if parser_name:
                            tables = pd.read_html(html_io, flavor=parser_name)
                            parser_used = parser_name
                            break
                        else:
                            tables = pd.read_html(html_io)
                            parser_used = 'default'
                            break
                    except Exception as e:
                        last_error = str(e)
                        continue
                
                if tables is None:
                    raise Exception(f"모든 파서 실패. 마지막 오류: {last_error}")
                
                tickers_from_this_source = 0
                
                # 각 테이블에서 티커 컬럼 찾기
                for table_idx, table in enumerate(tables):
                    # 티커 컬럼 이름 후보들 (더 많은 변형 포함)
                    ticker_columns = [
                        "Symbol", "Ticker", "Ticker symbol", "Symbols", "Code",
                        "Ticker symbol", "Ticker Symbol", "SYMBOL", "TICKER",
                        # S&P 500의 경우 "Symbol"이 첫 번째 컬럼일 수 있음
                    ]
                    
                    # MultiIndex 컬럼 처리 (튜플로 된 컬럼명)
                    if isinstance(table.columns, pd.MultiIndex):
                        # 첫 번째 레벨만 사용
                        table.columns = table.columns.get_level_values(0)

                    # 국가 정보를 담고 있을 수 있는 컬럼 후보
                    country_columns = [
                        col for col in table.columns
                        if any(key in str(col).lower() for key in ["country", "headquarters", "headquarter", "location"])
                    ]
                    
                    def _process_row(row, ticker_value, row_country_override=None):
                        nonlocal tickers_from_this_source
                        if pd.isna(ticker_value):
                            return
                        ticker_str = str(ticker_value).strip().upper()
                        ticker_str = ticker_str.split()[0] if ticker_str else ""
                        ticker_str = ticker_str.replace("(", "").replace(")", "")
                        if not ticker_str:
                            return

                        # 행 단위 국가 정보 우선 사용, 없으면 기본 country
                        row_country = row_country_override or country
                        if country_columns:
                            for ccol in country_columns:
                                try:
                                    cval = row.get(ccol)
                                except Exception:
                                    cval = None
                                if cval is not None and not pd.isna(cval):
                                    cval_str = str(cval).strip()
                                    if cval_str:
                                        row_country = cval_str
                                        break

                        normalized_ticker = _apply_country_suffix(ticker_str, row_country)
                        if normalized_ticker:
                            all_tickers_map[normalized_ticker] = row_country or country
                            tickers_from_this_source += 1
                    
                    found_column = None
                    for col_name in ticker_columns:
                        # 정확한 매칭과 부분 매칭 모두 시도
                        matching_cols = [col for col in table.columns if str(col).upper() == col_name.upper() or col_name.upper() in str(col).upper()]
                        if matching_cols:
                            found_column = matching_cols[0]
                            # 티커 추출 및 정제
                            for _, row in table.iterrows():
                                try:
                                    _process_row(row, row[found_column])
                                except Exception:
                                    continue
                            break  # 티커 컬럼을 찾으면 다음 테이블로
                    
                    # 티커 컬럼을 찾지 못한 경우, 인덱스 4번째 컬럼 확인 (DAX 등)
                    if found_column is None and len(table.columns) > 4:
                        try:
                            # 인덱스 4 (0-기반)에 Ticker 컬럼이 있는지 확인
                            col_at_index_4 = table.columns[4]
                            if 'ticker' in str(col_at_index_4).lower() or 'symbol' in str(col_at_index_4).lower():
                                found_column = col_at_index_4
                                for _, row in table.iterrows():
                                    try:
                                        _process_row(row, row[found_column])
                                    except Exception:
                                        continue
                        except (IndexError, KeyError):
                            pass
                    
                    # 첫 번째 컬럼이 짧은 문자열이고 숫자가 아닌 경우 티커일 수 있음 (S&P 500 등)
                    if found_column is None and len(table.columns) > 0:
                        first_col = table.columns[0]
                        # 첫 번째 컬럼의 샘플 값 확인
                        sample_values = table[first_col].dropna().head(5).astype(str)
                        # 대부분이 1-5자 길이의 영문 대문자인 경우 티커일 가능성
                        if len(sample_values) > 0:
                            ticker_like = sum(1 for v in sample_values if 1 <= len(v.strip()) <= 5 and v.strip().isalpha())
                            if ticker_like >= len(sample_values) * 0.8:  # 80% 이상이 티커처럼 보이면
                                found_column = first_col
                                for _, row in table.iterrows():
                                    try:
                                        _process_row(row, row[first_col])
                                    except Exception:
                                        continue
                
                if tickers_from_this_source > 0:
                    success_count += 1
                    error_details.append(f"✅ {url}: {len(tables)}개 테이블 ({parser_used}), {tickers_from_this_source}개 티커 추출")
                else:
                    fail_count += 1
                    # 테이블 컬럼 정보도 출력
                    table_info = []
                    for idx, table in enumerate(tables[:3]):  # 최대 3개 테이블만
                        table_info.append(f"테이블{idx+1}: {list(table.columns)[:5]}")
                    error_details.append(f"⚠️  {url}: {len(tables)}개 테이블 발견했으나 티커 컬럼을 찾지 못함 ({', '.join(table_info)})")
                
            except Exception as e:
                fail_count += 1
                import traceback
                error_msg = f"❌ {url}: {type(e).__name__}: {str(e)[:200]}"
                error_details.append(error_msg)
                # 모든 오류의 상세 정보 포함 (최대 300자)
                tb_str = traceback.format_exc()
                if len(tb_str) > 300:
                    tb_str = tb_str[:300] + "..."
                error_details.append(f"   상세: {tb_str}")
                continue
        
        # 중복 제거 및 정렬
        unique_tickers_map = dict(sorted(all_tickers_map.items()))
        
        return unique_tickers_map, {
            "success_count": success_count,
            "fail_count": fail_count,
            "total_tickers": len(unique_tickers_map),
            "error_details": error_details
        }

    result_map, details = await asyncio.to_thread(_sync_job)
    
    # 결과 로깅
    logger.info(f"   📊 수집 결과: 성공 {details['success_count']}개, 실패 {details['fail_count']}개")
    for detail in details['error_details']:
        logger.info(f"   {detail}")
    
    if len(result_map) > 0:
        logger.info(f"✅ [Step 1] 티커 수집 완료: {len(result_map)}개 티커 수집됨")
        # 샘플 티커 로깅 변경
        sample_tickers = [f"{t} ({c})" for t, c in list(result_map.items())[:10]]
        logger.info(f"   샘플 티커 (최대 10개): {', '.join(sample_tickers)}")
    else:
        logger.error(f"❌ [Step 1] 티커 수집 실패: 0개 티커 수집됨")
        logger.error("   가능한 원인:")
        logger.error("     1. 네트워크 연결 문제")
        logger.error("     2. 위키피디아 페이지 구조 변경")
        logger.error("     3. pandas.read_html 라이브러리 문제")
        logger.error("     4. 방화벽/프록시 설정 문제")
    
    return result_map


async def _fetch_single_ticker_yf(ticker: str) -> Optional[Dict[str, Any]]:
    """yfinance로 단일 티커의 시가총액 / 가격 / 회사 정보 조회. (국가 정보 수집 로직 제거)"""

    def _sync_job() -> Optional[Dict[str, Any]]:
        import logging
        import random
        import time

        logger = logging.getLogger(__name__)
        max_attempts = 3
        last_error: Optional[Exception] = None

        for attempt in range(1, max_attempts + 1):
            info: Dict[str, Any] = {}
            try:
                t = yf.Ticker(ticker)
                info = t.info or {}
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[yf] {ticker} info fetch failed (try {attempt}/{max_attempts}): "
                    f"{type(e).__name__}: {str(e)[:150]}"
                )

            market_cap = info.get("marketCap")
            price = info.get("currentPrice") or info.get("regularMarketPrice")

            if market_cap is not None or price is not None:
                data: Dict[str, Any] = {
                    "ticker": ticker,
                    "name": info.get("longName") or info.get("shortName") or ticker,
                    "sector": info.get("sector"),
                    "industry": info.get("industry"),
                    "currency": info.get("currency"),
                    # 현지통화 기준 시가총액 (원본)
                    "market_cap_local": float(market_cap) if market_cap is not None else None,
                    "price": float(price) if price is not None else None,
                    "volume": info.get("volume"),
                }
                # market_cap는 하위 호환성을 위해 유지
                data["market_cap"] = data["market_cap_local"]
                return data

            if attempt < max_attempts:
                delay = random.uniform(1, 2)
                logger.warning(
                    f"[yf] {ticker} missing marketCap/price (try {attempt}/{max_attempts}); "
                    f"retrying in {delay:.1f}s"
                )
                time.sleep(delay)

        if last_error:
            logger.warning(
                f"[yf] {ticker} failed after {max_attempts} tries: "
                f"{type(last_error).__name__}: {str(last_error)[:150]}"
            )
        else:
            logger.warning(f"[yf] {ticker} missing marketCap/price after {max_attempts} tries")
        return None

    data = await asyncio.to_thread(_sync_job)
    if data is None:
        return None

    market_cap_local = data.get("market_cap_local")
    currency = data.get("currency") or "USD"

    if market_cap_local is not None:
        rate = await get_usd_exchange_rate(currency)
        data["market_cap_usd"] = market_cap_local * rate
    else:
        data["market_cap_usd"] = None

    return data


async def _fetch_company_logo_fmp(ticker: str, company_name: Optional[str] = None) -> Optional[str]:
    """
    기업 로고 URL을 가져옵니다.
    
    전략:
    - FMP Image API URL을 직접 조립해 HEAD로 존재 여부 확인
    - 필요 시 GET(stream=True)로 Content-Type을 재확인
    - 200이며 Content-Type이 image/*이면 성공, 그 외(404 포함)는 실패 처리
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not settings.fmp_api_key:
        logger.debug("FMP API Key 없음: 로고 수집 건너뜀")
        return None
    
    def _try_fmp_image_api() -> Optional[str]:
        session = _get_fmp_session()
        normalized_ticker = ticker.upper()
        image_url = f"https://financialmodelingprep.com/image-stock/{normalized_ticker}.png?apikey={settings.fmp_api_key}"

        # 1차: HEAD로 존재 여부 확인 (redirect 허용)
        try:
            head_resp = session.head(image_url, allow_redirects=True, timeout=5)
            status = head_resp.status_code
            content_type = head_resp.headers.get("Content-Type", "").lower()
            head_resp.close()

            if status == 200 and content_type.startswith("image/"):
                logger.debug(f"FMP Direct URL Strategy: {normalized_ticker} HEAD 확인 성공 (ct={content_type})")
                return image_url
        except Exception as e:
            logger.debug(f"FMP Direct URL Strategy HEAD 오류 ({ticker}): {type(e).__name__}: {str(e)[:100]}")

        # 2차: GET(stream=True)로 실제 콘텐츠 확인
        try:
            with session.get(image_url, stream=True, timeout=5) as resp:
                status = resp.status_code
                content_type = resp.headers.get("Content-Type", "").lower()
                is_image = content_type.startswith("image/")

                if status == 200 and is_image:
                    logger.debug(f"FMP Direct URL Strategy: {normalized_ticker} 로고 수집 성공 (ct={content_type})")
                    return image_url

                logger.debug(f"FMP Direct URL Strategy: {normalized_ticker} 실패 (status={status}, ct={content_type})")
                return None
        except Exception as e:
            logger.debug(f"FMP Direct URL Strategy 오류 ({ticker}): {type(e).__name__}: {str(e)[:100]}")
            return None
    
    return await asyncio.to_thread(_try_fmp_image_api)


async def fetch_top_100_data(tickers_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    수집된 티커 목록에 대해 yfinance를 사용하여 시가총액 / 가격을 조회하고,
    시가총액(USD 기준) 상위 100개를 반환합니다.
    FMP API를 사용하여 로고 URL도 함께 수집합니다.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    tickers = list(tickers_map.keys())
    total_tickers = len(tickers)
    
    logger.info(f"📊 [Step 2] 데이터 수집 시작: {total_tickers}개 티커 스캔")
    logger.info(f"   전략: fast_info 우선 스캔 (배치 처리) → Top 100 상세 조회")

    async def _fetch_fast_marketcap(ticker: str) -> Optional[Dict[str, Any]]:
        def _sync_fast() -> Optional[Dict[str, Any]]:
            try:
                t = yf.Ticker(ticker)
                fi = getattr(t, "fast_info", None)
                if not fi:
                    return None
                mc = getattr(fi, "market_cap", None)
                if mc is None:
                    return None
                return {
                    "ticker": ticker,
                    "market_cap_local": float(mc),
                    "price": getattr(fi, "last_price", None),
                    "currency": getattr(fi, "currency", None),
                    "volume": getattr(fi, "last_volume", None),
                    "name": ticker,
                    "sector": None,
                    "industry": None,
                }
            except Exception as e:
                logger.warning(f"⚠️ {ticker} fast_info 실패: {e}")
                raise

        # fast_info도 네트워크 요청이므로 비동기로 실행
        fast = await asyncio.to_thread(_sync_fast)
        if not fast:
            return None

        currency = fast.get("currency") or "USD"
        rate = await get_usd_exchange_rate(currency)
        fast["market_cap_usd"] = fast["market_cap_local"] * rate
        fast["market_cap"] = fast["market_cap_local"]
        return fast

    # ---------------------------------------------------------
    # [수정됨] 1차: fast_info 스캔에도 배치 처리 적용 (과부하 방지)
    # ---------------------------------------------------------
    fast_valid: List[Dict[str, Any]] = []
    fast_map: Dict[str, Dict[str, Any]] = {}
    failed_fast_scan_tickers: List[str] = []
    
    # 한 번에 50개씩 스캔
    SCAN_BATCH_SIZE = 50
    
    for i in range(0, total_tickers, SCAN_BATCH_SIZE):
        batch_tickers = tickers[i : i + SCAN_BATCH_SIZE]
        logger.info(f"   🔍 1차 스캔 배치: {i+1}~{min(i+SCAN_BATCH_SIZE, total_tickers)}/{total_tickers}")
        
        tasks = [asyncio.create_task(_fetch_fast_marketcap(t)) for t in batch_tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                failed_fast_scan_tickers.append(batch_tickers[idx])
                continue
            if res and res.get("market_cap_usd") is not None:
                fast_valid.append(res)
                fast_map[res["ticker"]] = res
        
        # 배치 간 짧은 대기 (서버 부하 완화)
        if i + SCAN_BATCH_SIZE < total_tickers:
            await asyncio.sleep(1.0)

    if not fast_valid:
        logger.error("❌ fast_info 기반 스캔 실패: 유효한 시가총액 데이터를 찾지 못했습니다.")
        return []

    # 시가총액 내림차순 정렬
    fast_valid.sort(key=lambda x: x["market_cap_usd"] or 0.0, reverse=True)
    top_fast = fast_valid[:100]
    top_fast_tickers = [item["ticker"] for item in top_fast]

    logger.info(f"✅ 1차 스캔 완료: 유효 {len(fast_valid)}개 중 상위 100개 선정")

    # ---------------------------------------------------------
    # 2차: Top 100만 상세 조회 (필요 시 .info Fallback)
    # ---------------------------------------------------------
    DETAIL_BATCH_SIZE = 10  # 상세 조회는 더 조심스럽게 (10개씩)
    detailed_results: List[Optional[Dict[str, Any]]] = []
    
    detail_candidates = top_fast_tickers + [
        t for t in failed_fast_scan_tickers if t not in top_fast_tickers
    ]

    for batch_start in range(0, len(detail_candidates), DETAIL_BATCH_SIZE):
        batch_end = min(batch_start + DETAIL_BATCH_SIZE, len(detail_candidates))
        batch_tickers = detail_candidates[batch_start:batch_end]

        logger.info(f"   📝 상세 정보 수집: {batch_start + 1}~{batch_end}/{len(detail_candidates)}")

        async def _fetch_with_fallback(ticker: str):
            try:
                # 상세 정보(.info) 시도 -> 실패 시 fast_info 데이터 사용 (순위 유지 목적)
                detailed = await _fetch_single_ticker_yf(ticker)
                return detailed or fast_map.get(ticker)
            except Exception as e:
                return fast_map.get(ticker)

        batch_tasks = [asyncio.create_task(_fetch_with_fallback(t)) for t in batch_tickers]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

        for idx, res in enumerate(batch_results):
            if isinstance(res, Exception):
                res = fast_map.get(batch_tickers[idx])
            detailed_results.append(res)

        # 상세 조회 배치 간 대기 (Rate Limit 방지)
        if batch_end < len(top_fast_tickers):
            await asyncio.sleep(2.0)

    # 유효 데이터 필터링
    valid_items: List[Dict[str, Any]] = [
        r for r in detailed_results
        if r is not None and r.get("market_cap_usd") is not None
    ]

    valid_items.sort(key=lambda x: x["market_cap_usd"] or 0.0, reverse=True)
    top_100 = valid_items[:100]

    # 국가 정보 매핑
    country_count = 0
    for item in top_100:
        ticker = item["ticker"]
        country = tickers_map.get(ticker)
        if country:
            item["country"] = country
            country_count += 1
    
    # ---------------------------------------------------------
    # 3차: 로고 수집 (FMP)
    # ---------------------------------------------------------
    if top_100:
        logger.info(f"🖼️  [Step 3] 로고 수집 시작 ({len(top_100)}개)")
        
        LOGO_BATCH_SIZE = 10
        logo_results = []
        
        for batch_start in range(0, len(top_100), LOGO_BATCH_SIZE):
            batch_end = min(batch_start + LOGO_BATCH_SIZE, len(top_100))
            batch_items = top_100[batch_start:batch_end]
            
            # 병렬 처리
            tasks = [
                asyncio.create_task(_fetch_company_logo_fmp(item["ticker"], item.get("name")))
                for item in batch_items
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                if isinstance(res, Exception):
                    logo_results.append(None)
                else:
                    logo_results.append(res)
            
            if batch_end < len(top_100):
                await asyncio.sleep(0.2)
        
        # 결과 매핑
        for item, logo_url in zip(top_100, logo_results):
            item["logo_url"] = logo_url

    logger.info(f"✅ [Step 2] 데이터 수집 완료: 최종 {len(top_100)}개")
    return top_100


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
            # country 업데이트: item에 country가 있으면 업데이트 (None이어도 명시적으로 설정)
            if "country" in item:
                company.country = item.get("country")
            company.currency = item.get("currency") or company.currency
            # 로고 URL 업데이트: item에 logo_url이 있으면 업데이트 (None이어도 명시적으로 설정)
            if "logo_url" in item:
                company.logo_url = item.get("logo_url")
        else:
            company = models.Company(
                ticker=ticker,
                name=item.get("name") or ticker,
                sector=item.get("sector"),
                industry=item.get("industry"),
                country=item.get("country"),
                currency=item.get("currency"),
                logo_url=item.get("logo_url"),
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


async def collect_and_update_global_top_100(db: AsyncSession, limit: int = None) -> Dict[str, Any]:
    """
    글로벌 상위 100개 기업 수집 및 DB 업데이트 (Company, Ranking, Price)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("="*70)
    logger.info("🚀 [글로벌 상위 100개 기업 재조사] 시작")
    
    # 1. 티커 수집
    tickers_map = await fetch_index_tickers()
    tickers = list(tickers_map.keys())
    
    if limit and limit > 0:
        tickers = tickers[:limit]
        tickers_map = {t: tickers_map[t] for t in tickers if t in tickers_map}
        logger.info(f"   ⚠️ 테스트 모드: {limit}개 티커만 처리")

    if not tickers:
        logger.error("❌ 티커 수집 실패")
        return {"top_100": [], "ranking_date": datetime.now(timezone.utc).date(), "changes": {}}

    # 2. 데이터 수집 (yfinance + FMP logo)
    top_100 = await fetch_top_100_data(tickers_map)
    ranking_date = datetime.now(timezone.utc).date()
    
    if not top_100:
        logger.error("❌ 데이터 수집 실패 (결과 없음)")
        return {"top_100": [], "ranking_date": ranking_date, "changes": {}}

    # 3. 변동 데이터 계산
    logger.info(f"📊 [Step 4-1] 랭킹 변동 계산 중...")
    changes = await _calculate_ranking_changes(db, top_100, ranking_date)

    # 4. DB 저장 시작
    logger.info(f"💾 [Step 4] DB 저장 트랜잭션 시작 (기업: {len(top_100)}개)")
    
    try:
        current_year = ranking_date.year
        tickers_list = [item["ticker"] for item in top_100]

        # [4-2] Company Update
        stmt = select(models.Company).where(models.Company.ticker.in_(tickers_list))
        result = await db.execute(stmt)
        existing_companies = {c.ticker: c for c in result.scalars().all()}
        
        for item in top_100:
            ticker = item["ticker"]
            if ticker in existing_companies:
                c = existing_companies[ticker]
                c.name = item.get("name") or c.name
                c.sector = item.get("sector") or c.sector
                c.industry = item.get("industry") or c.industry
                c.currency = item.get("currency") or c.currency
                if item.get("country"): c.country = item.get("country")
                if item.get("logo_url"): c.logo_url = item.get("logo_url")
            else:
                new_c = models.Company(
                    ticker=ticker,
                    name=item.get("name") or ticker,
                    sector=item.get("sector"),
                    industry=item.get("industry"),
                    country=item.get("country"),
                    currency=item.get("currency"),
                    logo_url=item.get("logo_url"),
                )
                db.add(new_c)
        
        # [4-3] Rankings Update (Delete & Insert)
        logger.info(f"💾 [Step 4-3] Rankings 업데이트 (Date: {ranking_date})")
        await db.execute(delete(models.Ranking).where(models.Ranking.ranking_date == ranking_date))
        
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

        # [4-4] Prices Update (Upsert)
        logger.info(f"💾 [Step 4-4] Prices 업데이트 (Date: {ranking_date})")
        price_datetime = datetime(ranking_date.year, ranking_date.month, ranking_date.day, tzinfo=timezone.utc)
        
        # 일괄 처리를 위해 기존 데이터 로드 (성능 최적화)
        price_stmt = select(models.Price).where(
            models.Price.ticker.in_(tickers_list),
            models.Price.date == price_datetime
        )
        price_result = await db.execute(price_stmt)
        existing_prices = {p.ticker: p for p in price_result.scalars().all()}
        
        prices_added = 0
        prices_updated = 0
        
        for item in top_100:
            ticker = item["ticker"]
            if ticker in existing_prices:
                p = existing_prices[ticker]
                p.close = item.get("price")
                p.market_cap = item.get("market_cap_usd")
                p.volume = item.get("volume")
                prices_updated += 1
            else:
                new_p = models.Price(
                    ticker=ticker,
                    date=price_datetime,
                    close=item.get("price"),
                    market_cap=item.get("market_cap_usd"),
                    volume=item.get("volume")
                )
                db.add(new_p)
                prices_added += 1
        
        logger.info(f"   Prices 결과: 신규 {prices_added}개, 업데이트 {prices_updated}개")

        # [4-5] 트랜잭션 커밋
        await db.commit()
        logger.info("✅ [Step 4] DB 저장 완료!")

        # [4-6] AI 트렌드 분석 (저장 후 실행)
        try:
            ai_trend_text = await ai_client.generate_sector_trend_analysis(changes)
            sector_trend = models.SectorTrend(
                date=ranking_date,
                dominant_sectors=changes.get("sector_stats"),
                new_entries={"new": changes.get("new_entries"), "exited": changes.get("exited")},
                ai_analysis_text=ai_trend_text,
            )
            db.add(sector_trend)
            await db.commit()
            logger.info("✅ 섹터 트렌드 AI 분석 저장 완료")
        except Exception as e:
            logger.warning(f"⚠️ 섹터 트렌드 저장 실패: {e}")

    except Exception as e:
        logger.error(f"❌ DB 저장 중 치명적 오류: {e}")
        await db.rollback()
        import traceback
        logger.error(traceback.format_exc())
        return {"top_100": [], "ranking_date": ranking_date, "changes": {}}
    
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
                    models.MarketReport.source_type == "daily_update",
                    models.MarketReport.collected_at >= today_start,
                    models.MarketReport.collected_at <= today_end,
                )
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
                        source_type="daily_update",
                        raw_data=report_data["raw_data"],
                        summary_content=report_data["summary_content"],
                        sentiment_score=report_data["sentiment_score"],
                        content="See raw_data or summary_content"
                    )
                    db.add(report)
                
                collected_count += 1
                
            except Exception as e:
                logger.error(f"뉴스 저장 실패 ({ticker}): {type(e).__name__}: {e}")
                failed_count += 1
                continue
        
        # 배치마다 커밋
        try:
            await db.commit()
        except Exception as e:
            logger.error(f"배치 커밋 실패: {type(e).__name__}: {e}")
            await db.rollback()
        
        # 배치 간 대기 (Rate Limit 방지)
        if batch_end < len(tickers):
            await asyncio.sleep(2)
    
    logger.info(f"뉴스 수집 완료: {collected_count}개 성공, {failed_count}개 실패")
    return collected_count


async def collect_daily_prices(db: AsyncSession) -> int:
    """
    상위 100개 기업의 일별 주가·시가총액·거래량을 수집하여 Price 테이블에 저장합니다. (일별 실행)
    
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
    today = datetime.now(timezone.utc).date()
    price_date = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    
    logger.info(f"일별 주가 수집 시작: {len(tickers)}개 기업")
    
    collected_count = 0
    
    # 병렬로 데이터 수집
    tasks = [asyncio.create_task(_fetch_single_ticker_yf(t)) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception) or result is None:
            continue
        
        try:
            # 기존 가격 데이터 확인
            stmt = select(models.Price).where(
                models.Price.ticker == ticker,
                models.Price.date == price_date,
            )
            result_query = await db.execute(stmt)
            existing_price = result_query.scalar_one_or_none()
            
            if existing_price:
                # 업데이트
                existing_price.close = result.get("price")
                existing_price.market_cap = result.get("market_cap_usd")
                existing_price.volume = result.get("volume")
            else:
                # 신규 생성
                price = models.Price(
                    ticker=ticker,
                    date=price_date,
                    close=result.get("price"),
                    market_cap=result.get("market_cap_usd"),
                    volume=result.get("volume"),
                )
                db.add(price)
            
            collected_count += 1
            
        except Exception as e:
            logger.error(f"주가 저장 실패 ({ticker}): {type(e).__name__}: {e}")
            continue
    
    await db.commit()
    logger.info(f"일별 주가 수집 완료: {collected_count}개")
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


async def collect_quarterly_reports(db: AsyncSession) -> int:
    """
    상위 100개 기업의 분기별 리포트를 생성하여 QuarterlyReport 테이블에 저장합니다. (분기별 실행)
    
    Returns:
        생성한 리포트 수
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
    
    # 현재 분기 계산 (1~4)
    now = datetime.now(timezone.utc)
    current_quarter = (now.month - 1) // 3 + 1
    
    logger.info(f"분기별 리포트 생성 시작: {len(tickers)}개 기업, {current_year}년 {current_quarter}분기")
    
    generated_count = 0
    failed_count = 0
    
    for ticker in tickers:
        try:
            # 기존 리포트 확인
            stmt = select(models.QuarterlyReport).where(
                models.QuarterlyReport.ticker == ticker,
                models.QuarterlyReport.year == current_year,
                models.QuarterlyReport.quarter == current_quarter
            )
            result = await db.execute(stmt)
            existing_report = result.scalar_one_or_none()
            
            # 이미 리포트가 있으면 건너뛰기
            if existing_report:
                continue
            
            # 재무 데이터 조회
            stmt = select(models.Financial).where(
                models.Financial.ticker == ticker,
                models.Financial.year == current_year,
                models.Financial.quarter == current_quarter
            )
            result = await db.execute(stmt)
            financial = result.scalar_one_or_none()
            
            if not financial:
                # 재무 데이터가 없으면 건너뛰기
                continue
            
            # 재무 데이터 딕셔너리 구성
            financials_dict = {
                "year": financial.year,
                "revenue": financial.revenue,
                "net_income": financial.net_income,
                "per": financial.per,
                "market_cap": financial.market_cap,
            }
            
            # 최근 뉴스 조회 (최근 3개월)
            three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)
            stmt = select(models.MarketReport).where(
                models.MarketReport.ticker == ticker,
                models.MarketReport.collected_at >= three_months_ago
            ).order_by(models.MarketReport.collected_at.desc()).limit(5)
            result = await db.execute(stmt)
            market_reports = result.scalars().all()
            
            # 뉴스 리스트 구성
            news_list = []
            for report in market_reports:
                if report.summary_content:
                    news_list.append({
                        "title": f"Market Report ({report.collected_at.date()})",
                        "body": report.summary_content,
                        "date": report.collected_at.isoformat(),
                    })
            
            # AI로 분기별 리포트 생성
            try:
                report_content = await ai_client.generate_quarterly_report(
                    ticker=ticker,
                    year=current_year,
                    quarter=current_quarter,
                    financials=financials_dict,
                    news_list=news_list if news_list else None,
                )
                
                # QuarterlyReport 저장
                quarterly_report = models.QuarterlyReport(
                    ticker=ticker,
                    year=current_year,
                    quarter=current_quarter,
                    content=report_content,
                )
                db.add(quarterly_report)
                generated_count += 1
                
            except Exception as e:
                logger.error(f"분기별 리포트 생성 실패 ({ticker}): {type(e).__name__}: {e}")
                failed_count += 1
                continue
                
        except Exception as e:
            logger.error(f"분기별 리포트 처리 실패 ({ticker}): {type(e).__name__}: {e}")
            failed_count += 1
            continue
    
    await db.commit()
    logger.info(f"분기별 리포트 생성 완료: {generated_count}개 생성, {failed_count}개 실패")
    return generated_count
