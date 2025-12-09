"""
로고 수집 문제 진단 테스트 스크립트

이 스크립트는 FMP API 로고 수집이 실패하는 원인을 진단합니다.
DEBUG 레벨 로깅을 활성화하여 상세한 오류 메시지를 확인할 수 있습니다.

사용법:
    python backend/test/test_logo_collection.py
"""

import asyncio
import sys
from pathlib import Path
import logging

from sqlalchemy import select

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# DEBUG 레벨 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app import models
from app.database import async_session_factory
from app.services.collection_service import _fetch_company_logo_fmp


async def _load_test_cases_from_db(limit: int = 20, missing_only: bool = True):
    """
    DB에 저장된 기업 데이터를 기반으로 테스트 케이스를 만든다.
    - missing_only=True: logo_url이 비어 있는 기업만 대상으로 함.
    - limit: 조회할 기업 수.
    """
    logger = logging.getLogger(__name__)
    try:
        async with async_session_factory() as db:
            stmt = select(models.Company.ticker, models.Company.name)
            if missing_only:
                stmt = stmt.where(
                    (models.Company.logo_url.is_(None)) | (models.Company.logo_url == "")
                )
            stmt = stmt.order_by(models.Company.ticker).limit(limit)
            result = await db.execute(stmt)
            rows = result.all()
            cases = [(row.ticker, row.name) for row in rows]
            if not cases:
                logger.warning("DB에서 로고 수집 대상 기업을 찾지 못했습니다. (fallback: 전체 기업 10개)")
                stmt = select(models.Company.ticker, models.Company.name).limit(10)
                result = await db.execute(stmt)
                rows = result.all()
                cases = [(row.ticker, row.name) for row in rows]
            return cases
    except Exception as e:
        logger.error(f"DB에서 테스트 케이스 로드 실패: {type(e).__name__}: {e}")
        raise


async def test_logo_collection():
    """로고 수집 테스트"""
    print("\n" + "="*70)
    print("🧪 로고 수집 진단 테스트")
    print("   전략: FMP Image API → DuckDuckGo 이미지 검색 fallback")
    print("="*70)
    
    print("⏳ DB에서 테스트 대상 기업 로드 중...")
    # 기본적으로 로고가 비어 있는 기업 20개를 대상으로 테스트
    test_cases = await _load_test_cases_from_db(limit=20, missing_only=True)
    
    print(f"\n📋 테스트 케이스: {len(test_cases)}개")
    for i, (ticker, name) in enumerate(test_cases, 1):
        print(f"   {i}. {ticker} ({name})")
    
    print("\n" + "-"*70)
    print("⏳ 로고 수집 시작...")
    print("   (DEBUG 레벨 로깅 활성화 - 상세 오류 메시지 확인 가능)")
    print("-"*70)
    
    results = {}
    
    for ticker, company_name in test_cases:
        print(f"\n🔍 테스트 중: {ticker} ({company_name})")
        try:
            logo_url = await _fetch_company_logo_fmp(ticker, company_name)
            results[ticker] = logo_url
            
            if logo_url:
                print(f"   ✅ 성공: {logo_url}")
            else:
                print(f"   ❌ 실패: None 반환 (위의 DEBUG 로그 확인)")
        except Exception as e:
            print(f"   ❌ 예외 발생: {type(e).__name__}: {e}")
            results[ticker] = None
    
    print("\n" + "="*70)
    print("📊 테스트 결과 요약")
    print("="*70)
    
    success_count = sum(1 for url in results.values() if url is not None)
    fail_count = len(results) - success_count
    
    print(f"\n✅ 성공: {success_count}/{len(results)}개")
    print(f"❌ 실패: {fail_count}/{len(results)}개")
    
    print("\n📋 상세 결과:")
    for ticker, logo_url in results.items():
        status = "✅" if logo_url else "❌"
        print(f"   {status} {ticker}: {logo_url or 'None'}")
    
    print("\n💡 참고:")
    print("   - DEBUG 레벨 로그에서 상세한 오류 메시지를 확인하세요")
    print("   - 전략: FMP Image API → DuckDuckGo 이미지 검색 fallback")
    print("   - FMP Image API 실패 시 자동으로 DuckDuckGo 이미지 검색 시도")
    print("   - HTTP 404: 티커를 찾을 수 없음 (FMP API가 해당 티커를 지원하지 않을 수 있음)")
    print("   - HTTP 401: API 키 인증 실패 (DuckDuckGo fallback 시도)")
    print("   - HTTP 429: Rate Limit 초과")
    print("   - .HK, .SZ, .T 같은 suffix가 있는 티커는 FMP API가 지원하지 않을 수 있지만,")
    print("     DuckDuckGo 이미지 검색으로 fallback하여 로고를 찾을 수 있습니다")
    
    return results


async def main():
    """메인 테스트 함수"""
    try:
        await test_logo_collection()
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

