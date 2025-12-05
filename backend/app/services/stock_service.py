import asyncio
from typing import Dict, List, Any
from datetime import datetime
import requests
import yfinance as yf


async def fetch_company_data(ticker: str) -> Dict[str, Any]:
    """
    yfinance를 사용하여 회사 정보와 재무 데이터를 비동기로 가져옵니다.
    
    Args:
        ticker: 주식 티커 심볼 (예: "AAPL", "MSFT")
    
    Returns:
        딕셔너리 형태:
        {
            "company": {
                "ticker": str,
                "name": str,
                "sector": str,
                "industry": str,
                "currency": str,
                ...
            },
            "financials": [
                {
                    "year": int,
                    "revenue": float,
                    "net_income": float,
                    "per": float,
                    "market_cap": float
                },
                ...
            ]
        }
    """
    
    def _fetch_sync(ticker: str) -> Dict[str, Any]:
        """동기 함수: yfinance로 데이터를 가져옵니다."""
        # requests.Session을 사용하여 User-Agent 설정 (봇 감지 방지)
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        
        ticker_obj = yf.Ticker(ticker, session=session)
        info = ticker_obj.info
        
        # Company 정보 추출
        company_data = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "currency": info.get("currency", ""),
        }
        
        # 재무 데이터 추출
        income_stmt = ticker_obj.income_stmt
        
        financials_list = []
        
        if income_stmt is not None and not income_stmt.empty:
            # 최근 3년치 데이터만 추출
            # income_stmt의 컬럼은 날짜이고, 행은 재무 항목
            # Total Revenue와 Net Income을 찾아야 함
            columns = income_stmt.columns[:3]  # 최근 3개 컬럼 (연도)
            
            for col in columns:
                year = None
                revenue = None
                net_income = None
                
                # 연도 추출 (날짜에서 연도만)
                if hasattr(col, 'year'):
                    year = col.year
                elif isinstance(col, str):
                    # 문자열인 경우 파싱 시도
                    try:
                        from datetime import datetime
                        year = datetime.strptime(col, "%Y-%m-%d").year
                    except:
                        pass
                
                # Revenue 찾기
                if "Total Revenue" in income_stmt.index:
                    revenue = income_stmt.loc["Total Revenue", col]
                elif "Revenue" in income_stmt.index:
                    revenue = income_stmt.loc["Revenue", col]
                
                # Net Income 찾기
                if "Net Income" in income_stmt.index:
                    net_income = income_stmt.loc["Net Income", col]
                elif "Net Income Common Stockholders" in income_stmt.index:
                    net_income = income_stmt.loc["Net Income Common Stockholders", col]
                
                # PER과 Market Cap은 info에서 가져옴 (연도별이 아닌 현재 값)
                per = info.get("trailingPE") or info.get("forwardPE")
                market_cap = info.get("marketCap")
                
                if year is not None:
                    financials_list.append({
                        "ticker": ticker,
                        "year": int(year),
                        "revenue": float(revenue) if revenue is not None and not (isinstance(revenue, float) and revenue != revenue) else None,
                        "net_income": float(net_income) if net_income is not None and not (isinstance(net_income, float) and net_income != net_income) else None,
                        "per": float(per) if per is not None else None,
                        "market_cap": float(market_cap) if market_cap is not None else None,
                    })
        
        # 연도순으로 정렬 (오래된 것부터)
        financials_list.sort(key=lambda x: x["year"])
        
        return {
            "company": company_data,
            "financials": financials_list
        }
    
    # asyncio.to_thread를 사용하여 동기 함수를 비동기로 실행
    return await asyncio.to_thread(_fetch_sync, ticker)

