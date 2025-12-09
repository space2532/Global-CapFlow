"""
티커 수집 테스트 스크립트
위키피디아에서 티커를 수집하는 기능을 직접 테스트합니다.
"""

import asyncio
import sys
from pathlib import Path
import logging

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

from app.services.collection_service import fetch_index_tickers


async def test_ticker_collection():
    """티커 수집 테스트"""
    print("\n" + "="*70)
    print("🧪 티커 수집 테스트")
    print("="*70)
    
    try:
        print("\n⏳ 티커 수집 시작...")
        result = await fetch_index_tickers()
        
        print(f"\n✅ 결과: {len(result)}개 티커 수집됨")
        
        if len(result) > 0:
            print(f"\n📋 샘플 티커 (최대 20개):")
            for i, ticker in enumerate(result[:20], 1):
                print(f"   {i}. {ticker}")
        else:
            print("\n❌ 티커 수집 실패!")
            print("\n💡 문제 해결 방법:")
            print("   1. 인터넷 연결 확인")
            print("   2. pandas, lxml, html5lib 라이브러리 설치 확인:")
            print("      pip install pandas lxml html5lib")
            print("   3. 방화벽/프록시 설정 확인")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_ticker_collection())


