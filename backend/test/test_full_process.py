import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging

# 프로젝트 루트 경로 추가
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.database import async_session_factory
from app.services.collection_service import (
    collect_and_update_global_top_100,
    collect_quarterly_financials,
    collect_news_for_top_100,
    collect_quarterly_reports
)

async def run_full_test():
    print("\n" + "="*70)
    print("🚀 [Global CapFlow] 전체 데이터 파이프라인 통합 테스트")
    print("="*70)
    print("   1. 글로벌 랭킹 & 주가 수집 (기본)")
    print("   2. 분기별 재무 데이터 수집 (Financials)")
    print("   3. 뉴스 수집 및 시장 요약 (Market Reports + AI)")
    print("   4. 분기별 심층 분석 리포트 생성 (Quarterly Reports + AI)")
    print("-" * 70)

    async with async_session_factory() as db:
        # [Step 1] 랭킹 및 기본 정보 수집
        print("\n⏳ [Step 1] 글로벌 100대 기업 랭킹 및 주가 수집 중...")
        # 테스트 시간을 줄이기 위해 20개만 수집하려면 limit=20 사용
        # 전체를 원하면 limit=None
        rank_result = await collect_and_update_global_top_100(db, limit=None) 
        print(f"   ✅ 랭킹 수집 완료: {len(rank_result['top_100'])}개 기업")

        # [Step 2] 재무 데이터 수집
        print("\n⏳ [Step 2] 분기별 재무 데이터(Financials) 수집 중...")
        fin_count = await collect_quarterly_financials(db)
        print(f"   ✅ 재무 데이터 저장 완료: {fin_count}개 기업 업데이트")

        # [Step 3] 뉴스 및 시장 리포트 (AI 요약 포함)
        print("\n⏳ [Step 3] 뉴스 수집 및 AI 시장 리포트 생성 중...")
        # (주의: OpenAI 비용 발생 가능, 시간이 오래 걸릴 수 있음)
        news_count = await collect_news_for_top_100(db)
        print(f"   ✅ 뉴스/리포트 저장 완료: {news_count}개 기업 처리")

        # [Step 4] 분기별 심층 리포트 (AI 분석)
        print("\n⏳ [Step 4] 분기별 AI 심층 분석 리포트 생성 중...")
        report_count = await collect_quarterly_reports(db)
        print(f"   ✅ 심층 리포트 생성 완료: {report_count}개 생성")

    print("\n" + "="*70)
    print("🎉 모든 테스트 과정이 완료되었습니다!")
    print("="*70)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_full_test())