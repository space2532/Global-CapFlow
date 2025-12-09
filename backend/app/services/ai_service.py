import asyncio
import json
import logging
from typing import Dict, List, Any

from openai import AsyncOpenAI, RateLimitError

from app.config import settings


logger = logging.getLogger(__name__)

print("📦 [AIService] Module imported.")  # 모듈 로드 확인용


class AIService:
    def __init__(self) -> None:
        """
        settings에 정의된 OpenAI API 키로 AsyncOpenAI 클라이언트를 초기화합니다.
        """
        api_key = settings.openai_api_key

        # 키 마스킹 (앞 5자리만 표시) - 디버깅용 로그
        masked = f"{api_key[:5]}..." if api_key else "None"
        print(f"✅ [AIService] Initialized. Key: {masked} (Type: {type(api_key)})")

        # 키가 없는 경우 generate 함수에서 처리할 수 있도록 None 허용
        self.client: AsyncOpenAI | None = (
            AsyncOpenAI(api_key=api_key) if api_key else None
        )

    async def generate_sector_trend_analysis(
        self,
        changes_data: Dict[str, Any],
    ) -> str:
        """
        글로벌 Top 100 랭킹 변동 데이터를 바탕으로 섹터 트렌드/자금 흐름을 3줄로 요약합니다.
        """
        default_result = "이번 달 트렌드 분석을 생성할 수 없습니다."

        if self.client is None:
            logger.warning("[AIService] OpenAI API 키가 설정되지 않아 섹터 트렌드 분석을 건너뜁니다.")
            return default_result

        client = self.client
        changes_text = json.dumps(changes_data or {}, ensure_ascii=False)

        system_prompt = (
            "너는 글로벌 시장 섹터 흐름을 해석하는 전문 투자 전략가다. "
            "데이터를 기반으로 간결하게 시그널을 뽑아내고, "
            "구조화된 3줄 요약으로 설명한다."
        )
        user_prompt = (
            f"이번 달 글로벌 100대 기업의 변동 사항이다. {changes_text} "
            "이를 바탕으로 주요 시장 트렌드와 섹터 자금 이동 흐름을 한국어로 3줄 요약해줘."
        )

        max_retries = 2
        wait_times = [2, 5]

        for attempt in range(max_retries):
            try:
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                )

                content = response.choices[0].message.content
                return content.strip() if content else default_result

            except RateLimitError:
                if attempt < max_retries - 1:
                    wait_sec = wait_times[attempt]
                    logger.warning(f"[AIService] Rate limit (trend). {wait_sec}s 후 재시도...")
                    await asyncio.sleep(wait_sec)
                else:
                    logger.error("[AIService] Rate limit으로 섹터 트렌드 생성 실패.")
            except Exception as e:
                logger.error(f"[AIService] 섹터 트렌드 생성 실패: {type(e).__name__}: {e}")
                break

        return default_result

    async def generate_market_summary(
        self,
        ticker: str,
        news_list: List[Dict[str, Any]],
        financials: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        수집된 뉴스 데이터와 재무 데이터를 OpenAI(GPT-4o)에게 보내서,
        투자 관점의 요약과 감성 점수를 추출하는 비동기 메서드.

        기존 함수형 구현의 에러 처리 및 반환 포맷을 그대로 유지합니다.
        """

        # 기본값 설정
        default_result = {
            "summary": "분석 실패",
            "sentiment_score": 0.0,
        }

        print(f"🚀 [AIService] Generating summary for {ticker}...")

        try:
            # API 키가 없거나 클라이언트 생성 실패 시
            if self.client is None:
                print("❌ [AIService] Client is None!")
                raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

            client = self.client

            # 뉴스 데이터를 텍스트로 변환
            news_text = ""
            if news_list:
                for idx, news in enumerate(news_list, 1):
                    title = news.get("title", "")
                    body = news.get("body", "") or news.get("snippet", "")
                    url = news.get("url", "")
                    source = news.get("source", "")
                    date = news.get("date", "")

                    news_text += f"\n[뉴스 {idx}]\n"
                    news_text += f"제목: {title}\n"
                    if body:
                        news_text += f"내용: {body}\n"
                    if url:
                        news_text += f"출처: {source} ({url})\n"
                    if date:
                        news_text += f"날짜: {date}\n"
            else:
                news_text = "수집된 뉴스가 없습니다."

            # 재무 데이터를 텍스트로 변환
            financials_text = ""
            if financials:
                revenue = financials.get("revenue")
                net_income = financials.get("net_income")
                per = financials.get("per")
                market_cap = financials.get("market_cap")

                revenue_str = f"{revenue:,.0f}" if revenue is not None else "N/A"
                net_income_str = f"{net_income:,.0f}" if net_income is not None else "N/A"
                per_str = f"{per:.2f}" if per is not None else "N/A"
                market_cap_str = f"{market_cap:,.0f}" if market_cap is not None else "N/A"

                financials_text = f"""
[재무 데이터]
- 매출(Revenue): {revenue_str}
- 순이익(Net Income): {net_income_str}
- PER: {per_str}
- 시가총액(Market Cap): {market_cap_str}
"""
            else:
                financials_text = "재무 데이터가 없습니다."

            # System 프롬프트
            system_prompt = """너는 냉철한 투자 애널리스트다. 주어진 뉴스들과 재무 데이터를 종합적으로 분석하여 다음 JSON 포맷으로 응답하라.

반드시 다음 형식을 정확히 따라야 한다:
{
    "summary": "시장 분위기와 주요 이슈를 3문장 이내로 요약 (한국어)",
    "sentiment_score": -1.0과 1.0 사이의 소수점 숫자 (-1.0: 매우 부정, 0.0: 중립, 1.0: 매우 긍정)
}

주의사항:
- summary는 반드시 한국어로 작성
- sentiment_score는 반드시 -1.0과 1.0 사이의 숫자여야 함
- JSON 형식만 반환하고, 추가 설명이나 마크다운 코드 블록 없이 순수 JSON만 반환"""

            # User 프롬프트
            user_prompt = f"""다음은 {ticker}에 대한 뉴스와 재무 데이터이다.

{news_text}

{financials_text}

위 정보를 종합하여 투자 관점에서 분석하고, JSON 형식으로 응답하라."""

            # OpenAI API 호출 (Rate Limit 재시도 로직 포함)
            print("⏳ [AIService] Calling OpenAI API...")
            
            max_retries = 3
            wait_times = [2, 5, 10]  # 1회차 2초, 2회차 5초, 3회차 10초
            
            response = None
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",  # 비용 절감을 위해 mini 모델 사용
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3,  # 일관성 있는 분석을 위해 낮은 temperature 사용
                    )
                    print("✅ [AIService] OpenAI Response received.")
                    break  # 성공 시 루프 종료
                    
                except RateLimitError as e:
                    last_exception = e
                    if attempt < max_retries - 1:  # 마지막 시도가 아니면
                        wait_seconds = wait_times[attempt]
                        print(f"⚠️ [AIService] Rate limit hit. Retrying in {wait_seconds}s... (Attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_seconds)
                    else:
                        # 3회 모두 실패
                        print(f"❌ [AIService] Rate limit error after {max_retries} attempts.")
                        raise
                except Exception as e:
                    # RateLimitError가 아닌 다른 예외는 즉시 재발생
                    last_exception = e
                    raise
            
            if response is None:
                raise last_exception if last_exception else Exception("Failed to get response from OpenAI API")

            # 응답 파싱
            content = response.choices[0].message.content
            if not content:
                logger.warning(f"[{ticker}] OpenAI 응답이 비어있습니다.")
                return default_result

            # JSON 파싱
            try:
                result = json.loads(content)

                # 필수 필드 검증
                summary = result.get("summary", "분석 실패")
                sentiment_score = result.get("sentiment_score", 0.0)

                # sentiment_score 범위 검증 및 보정
                if not isinstance(sentiment_score, (int, float)):
                    sentiment_score = 0.0
                else:
                    sentiment_score = float(sentiment_score)
                    # -1.0 ~ 1.0 범위로 제한
                    sentiment_score = max(-1.0, min(1.0, sentiment_score))

                return {
                    "summary": str(summary),
                    "sentiment_score": sentiment_score,
                }

            except json.JSONDecodeError as e:
                print(f"❌ [AIService] Error: {e} (JSONDecodeError)")
                return default_result

        except ValueError as e:
            # API 키가 없는 경우
            print(f"❌ [AIService] Error: {e}")
            return default_result

        except Exception as e:
            # 기타 예외 (네트워크 오류, API 오류 등)
            import traceback

            print(f"❌ [AIService] Error: {e}")
            # 터미널에 항상 상세 스택 트레이스를 출력
            traceback.print_exc()
            return default_result

    async def generate_matchup_report(
        self,
        tickers_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        여러 기업의 재무 데이터와 뉴스를 비교 분석하여 승자를 선정하고 근거를 제시하는 비동기 메서드.
        
        Args:
            tickers_data: 각 티커별 데이터를 담은 딕셔너리
                {
                    "AAPL": {
                        "financials": [...],
                        "news": [...],
                        "company": {...}
                    },
                    "TSLA": {
                        "financials": [...],
                        "news": [...],
                        "company": {...}
                    }
                }
        
        Returns:
            {
                "winner": "AAPL",
                "reason": "...",
                "summary": "...",
                "key_comparison": [
                    {
                        "metric": "매출",
                        "winner": "AAPL",
                        "reason": "..."
                    },
                    ...
                ]
            }
        """
        default_result = {
            "winner": "N/A",
            "reason": "분석 실패",
            "summary": "분석 실패",
            "key_comparison": [],
        }

        print(f"🚀 [AIService] Generating matchup report for {list(tickers_data.keys())}...")

        try:
            if self.client is None:
                print("❌ [AIService] Client is None!")
                raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

            client = self.client

            # 여러 기업의 데이터를 하나의 프롬프트 텍스트로 병합
            companies_text = ""
            ticker_list = list(tickers_data.keys())
            
            for ticker in ticker_list:
                data = tickers_data[ticker]
                company_info = data.get("company", {})
                financials_list = data.get("financials", [])
                news_list = data.get("news", [])
                
                companies_text += f"\n\n{'='*50}\n"
                companies_text += f"[기업: {ticker}]\n"
                companies_text += f"회사명: {company_info.get('name', 'N/A')}\n"
                companies_text += f"섹터: {company_info.get('sector', 'N/A')}\n"
                companies_text += f"산업: {company_info.get('industry', 'N/A')}\n"
                
                # 재무 데이터 (최근 데이터 우선)
                if financials_list:
                    latest_fin = financials_list[-1] if financials_list else {}
                    companies_text += f"\n[재무 데이터 (최근)]\n"
                    companies_text += f"- 연도: {latest_fin.get('year', 'N/A')}\n"
                    companies_text += f"- 매출(Revenue): {latest_fin.get('revenue', 'N/A'):,.0f}\n" if latest_fin.get('revenue') else "- 매출: N/A\n"
                    companies_text += f"- 순이익(Net Income): {latest_fin.get('net_income', 'N/A'):,.0f}\n" if latest_fin.get('net_income') else "- 순이익: N/A\n"
                    companies_text += f"- PER: {latest_fin.get('per', 'N/A'):.2f}\n" if latest_fin.get('per') else "- PER: N/A\n"
                    companies_text += f"- 시가총액(Market Cap): {latest_fin.get('market_cap', 'N/A'):,.0f}\n" if latest_fin.get('market_cap') else "- 시가총액: N/A\n"
                else:
                    companies_text += "\n[재무 데이터: 없음]\n"
                
                # 뉴스 데이터 (DB에서 가져온 경우 raw_data와 summary_content 사용)
                if news_list:
                    # DB에서 가져온 데이터인지 확인 (raw_data와 summary_content 키가 있는지)
                    if isinstance(news_list[0], dict) and "raw_data" in news_list[0] and "summary_content" in news_list[0]:
                        # DB에서 가져온 데이터: summary_content와 raw_data 사용
                        db_news = news_list[0]
                        companies_text += f"\n[뉴스 요약 (DB)]\n"
                        companies_text += f"요약: {db_news.get('summary_content', 'N/A')}\n"
                        companies_text += f"감성 점수: {db_news.get('sentiment_score', 0.0)}\n"
                        raw_data = db_news.get('raw_data', '')
                        if raw_data and raw_data != "No news collected for this date" and raw_data != "No news collected":
                            companies_text += f"\n[원문 메타데이터]\n{raw_data[:500]}...\n"  # 원문은 500자로 제한
                    else:
                        # 외부 API에서 가져온 원문 데이터
                        companies_text += f"\n[뉴스 ({len(news_list)}개)]\n"
                        for idx, news in enumerate(news_list[:5], 1):  # 최대 5개
                            title = news.get("title", "")
                            body = news.get("body", "") or news.get("snippet", "")
                            date = news.get("date", "")
                            companies_text += f"\n뉴스 {idx}:\n"
                            companies_text += f"  제목: {title}\n"
                            if body:
                                companies_text += f"  내용: {body[:200]}...\n"  # 내용은 200자로 제한
                            if date:
                                companies_text += f"  날짜: {date}\n"
                else:
                    companies_text += "\n[뉴스: 없음]\n"
            
            companies_text += f"\n{'='*50}\n"

            # System 프롬프트
            system_prompt = """너는 전문 투자 자문가다. 주어진 기업들의 데이터를 비교 분석하여 승자를 선정하고 근거를 제시해라. 반드시 JSON 포맷으로 답해라.

반드시 다음 형식을 정확히 따라야 한다:
{
    "winner": "티커 심볼 (예: AAPL)",
    "reason": "승자를 선정한 주요 이유를 2-3문장으로 설명 (한국어)",
    "summary": "전체 비교 분석 요약 (3-5문장, 한국어)",
    "key_comparison": [
        {
            "metric": "비교 지표명 (예: 매출, 순이익, PER, 시가총액, 성장성 등)",
            "winner": "해당 지표에서 우위인 티커",
            "reason": "해당 지표에서의 비교 결과 설명 (1-2문장, 한국어)"
        },
        ...
    ]
}

주의사항:
- winner는 반드시 제공된 티커 중 하나여야 함
- 모든 텍스트는 한국어로 작성
- key_comparison은 최소 3개 이상의 주요 지표를 비교해야 함
- JSON 형식만 반환하고, 추가 설명이나 마크다운 코드 블록 없이 순수 JSON만 반환"""

            # User 프롬프트
            user_prompt = f"""다음은 비교할 기업들의 데이터이다.

{companies_text}

위 정보를 종합하여 투자 관점에서 비교 분석하고, 승자를 선정하여 JSON 형식으로 응답하라."""

            # OpenAI API 호출 (Rate Limit 재시도 로직 포함)
            print("⏳ [AIService] Calling OpenAI API for matchup analysis...")
            
            max_retries = 3
            wait_times = [2, 5, 10]  # 1회차 2초, 2회차 5초, 3회차 10초
            
            response = None
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    response = await client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3,
                    )
                    print("✅ [AIService] OpenAI Response received for matchup.")
                    break  # 성공 시 루프 종료
                    
                except RateLimitError as e:
                    last_exception = e
                    if attempt < max_retries - 1:  # 마지막 시도가 아니면
                        wait_seconds = wait_times[attempt]
                        print(f"⚠️ [AIService] Rate limit hit. Retrying in {wait_seconds}s... (Attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_seconds)
                    else:
                        # 3회 모두 실패
                        print(f"❌ [AIService] Rate limit error after {max_retries} attempts.")
                        raise
                except Exception as e:
                    # RateLimitError가 아닌 다른 예외는 즉시 재발생
                    last_exception = e
                    raise
            
            if response is None:
                raise last_exception if last_exception else Exception("Failed to get response from OpenAI API")

            # 응답 파싱
            content = response.choices[0].message.content
            if not content:
                logger.warning("[Matchup] OpenAI 응답이 비어있습니다.")
                return default_result

            # JSON 파싱
            try:
                result = json.loads(content)

                # 필수 필드 검증
                winner = result.get("winner", "N/A")
                reason = result.get("reason", "분석 실패")
                summary = result.get("summary", "분석 실패")
                key_comparison = result.get("key_comparison", [])

                # winner가 제공된 티커 중 하나인지 검증
                if winner not in ticker_list:
                    print(f"⚠️ [AIService] Winner '{winner}' is not in ticker list. Using first ticker.")
                    winner = ticker_list[0] if ticker_list else "N/A"

                return {
                    "winner": str(winner),
                    "reason": str(reason),
                    "summary": str(summary),
                    "key_comparison": key_comparison if isinstance(key_comparison, list) else [],
                }

            except json.JSONDecodeError as e:
                print(f"❌ [AIService] Error: {e} (JSONDecodeError)")
                return default_result

        except ValueError as e:
            print(f"❌ [AIService] Error: {e}")
            return default_result

        except Exception as e:
            import traceback
            print(f"❌ [AIService] Error: {e}")
            traceback.print_exc()
            return default_result

    async def generate_quarterly_report(
        self,
        ticker: str,
        year: int,
        quarter: int,
        financials: Dict[str, Any],
        news_list: List[Dict[str, Any]] = None,
    ) -> str:
        """
        분기별 기업 분석 리포트를 생성하는 비동기 메서드.
        
        Args:
            ticker: 주식 티커 심볼 (예: "AAPL")
            year: 연도 (예: 2024)
            quarter: 분기 (1~4)
            financials: 재무 데이터 딕셔너리
            news_list: 뉴스 리스트 (선택사항)
        
        Returns:
            분기별 분석 리포트 텍스트 (한국어)
        """
        default_result = f"{year}년 {quarter}분기 {ticker} 분석 리포트를 생성할 수 없습니다."

        print(f"🚀 [AIService] Generating quarterly report for {ticker} ({year}Q{quarter})...")

        try:
            if self.client is None:
                print("❌ [AIService] Client is None!")
                raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

            client = self.client

            # 재무 데이터 텍스트 구성
            financials_text = ""
            if financials:
                financials_text = f"""
[재무 데이터]
- 연도: {financials.get('year', 'N/A')}
- 매출(Revenue): {financials.get('revenue', 'N/A'):,.0f}""" if financials.get('revenue') else "- 매출: N/A"
                financials_text += f"""
- 순이익(Net Income): {financials.get('net_income', 'N/A'):,.0f}""" if financials.get('net_income') else "\n- 순이익: N/A"
                financials_text += f"""
- PER: {financials.get('per', 'N/A'):.2f}""" if financials.get('per') else "\n- PER: N/A"
                financials_text += f"""
- 시가총액(Market Cap): {financials.get('market_cap', 'N/A'):,.0f}""" if financials.get('market_cap') else "\n- 시가총액: N/A"
            else:
                financials_text = "\n[재무 데이터: 없음]"

            # 뉴스 데이터 텍스트 구성
            news_text = ""
            if news_list:
                news_text = f"\n[뉴스 ({len(news_list)}개)]\n"
                for idx, news in enumerate(news_list[:5], 1):  # 최대 5개
                    title = news.get("title", "")
                    body = news.get("body", "") or news.get("snippet", "")
                    date = news.get("date", "")
                    news_text += f"\n뉴스 {idx}:\n"
                    news_text += f"  제목: {title}\n"
                    if body:
                        news_text += f"  내용: {body[:200]}...\n"
                    if date:
                        news_text += f"  날짜: {date}\n"
            else:
                news_text = "\n[뉴스: 없음]"

            # System 프롬프트
            system_prompt = """너는 전문 투자 분석가다. 주어진 기업의 분기별 재무 데이터와 뉴스를 종합 분석하여 상세한 분기 리포트를 작성해라.

리포트는 다음 구조를 따라야 한다:
1. 분기 개요 (2-3문장)
2. 재무 성과 분석 (매출, 순이익, PER 등 주요 지표 분석)
3. 주요 이슈 및 뉴스 분석
4. 전망 및 투자 의견 (2-3문장)

모든 내용은 한국어로 작성하고, 전문적이면서도 이해하기 쉽게 작성해라.
리포트는 500-800자 정도의 분량으로 작성해라."""

            # User 프롬프트
            user_prompt = f"""다음은 {ticker}의 {year}년 {quarter}분기 데이터이다.

{financials_text}

{news_text}

위 정보를 바탕으로 {year}년 {quarter}분기 종합 분석 리포트를 작성해라."""

            # OpenAI API 호출 (Rate Limit 재시도 로직 포함)
            print("⏳ [AIService] Calling OpenAI API for quarterly report...")
            
            max_retries = 3
            wait_times = [2, 5, 10]
            
            response = None
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    response = await client.chat.completions.create(
                        model="gpt-4o",  # 분기 리포트는 중요하므로 gpt-4o 사용
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.3,
                    )
                    print("✅ [AIService] OpenAI Response received for quarterly report.")
                    break
                    
                except RateLimitError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_seconds = wait_times[attempt]
                        print(f"⚠️ [AIService] Rate limit hit. Retrying in {wait_seconds}s... (Attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_seconds)
                    else:
                        print(f"❌ [AIService] Rate limit error after {max_retries} attempts.")
                        raise
                except Exception as e:
                    last_exception = e
                    raise
            
            if response is None:
                raise last_exception if last_exception else Exception("Failed to get response from OpenAI API")

            # 응답 파싱
            content = response.choices[0].message.content
            if not content:
                logger.warning(f"[Quarterly Report] OpenAI 응답이 비어있습니다.")
                return default_result

            return str(content)

        except ValueError as e:
            print(f"❌ [AIService] Error: {e}")
            return default_result

        except Exception as e:
            import traceback
            print(f"❌ [AIService] Error: {e}")
            traceback.print_exc()
            return default_result


ai_client = AIService()
