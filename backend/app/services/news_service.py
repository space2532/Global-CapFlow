import asyncio
from typing import List, Dict, Any
from duckduckgo_search import DDGS


async def fetch_company_news(ticker: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    duckduckgo-search를 사용하여 기업 관련 최신 뉴스를 비동기로 가져옵니다.
    
    Args:
        ticker: 주식 티커 심볼 (예: "AAPL", "MSFT")
        limit: 가져올 뉴스 기사 수 (기본값: 5)
    
    Returns:
        뉴스 기사들의 리스트. 각 항목은 다음 필드를 포함:
        {
            "title": str,      # 기사 제목
            "body": str,       # 기사 내용 요약
            "url": str,        # 기사 URL
            "source": str,     # 출처
            "date": str        # 날짜
        }
        검색 실패 시 빈 리스트 []를 반환합니다.
    """
    
    def _fetch_sync(ticker: str, limit: int) -> List[Dict[str, Any]]:
        """동기 함수: DDGS를 사용하여 뉴스를 가져옵니다."""
        try:
            with DDGS() as ddgs:
                # 검색 키워드: "{ticker} stock news" 또는 "{ticker} financial analysis"
                # 우선순위: stock news를 먼저 시도하고, 결과가 부족하면 financial analysis도 시도
                search_queries = [
                    f"{ticker} stock news",
                    f"{ticker} financial analysis"
                ]
                
                all_results = []
                
                for query in search_queries:
                    if len(all_results) >= limit:
                        break
                    
                    try:
                        # news() 메서드를 사용하여 뉴스 검색
                        results = list(ddgs.news(query, max_results=limit))
                        
                        for result in results:
                            # 중복 제거 (URL 기준)
                            if not any(item.get("url") == result.get("url", "") for item in all_results):
                                all_results.append(result)
                    except Exception:
                        # 개별 쿼리 실패 시 다음 쿼리 시도
                        continue
                
                # 결과를 표준 형식으로 변환
                news_list = []
                for result in all_results[:limit]:
                    news_item = {
                        "title": result.get("title", ""),
                        "body": result.get("body", "") or result.get("snippet", ""),
                        "url": result.get("url", "") or result.get("href", ""),
                        "source": result.get("source", "") or result.get("source_name", ""),
                        "date": result.get("date", "") or result.get("published", "")
                    }
                    news_list.append(news_item)
                
                return news_list
                
        except Exception:
            # 전체 검색 실패 시 빈 리스트 반환
            return []
    
    # asyncio.to_thread를 사용하여 동기 함수를 비동기로 실행
    return await asyncio.to_thread(_fetch_sync, ticker, limit)







