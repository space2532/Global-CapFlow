import json
import logging
from typing import Dict, List, Any

from openai import AsyncOpenAI

from ..config import settings


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

            # OpenAI API 호출
            print("⏳ [AIService] Calling OpenAI API...")
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # 일관성 있는 분석을 위해 낮은 temperature 사용
            )
            print("✅ [AIService] OpenAI Response received.")

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


ai_client = AIService()
