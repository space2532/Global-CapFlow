"""
배치 처리 및 Rate Limit 회피 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
1. 배치 처리 (20개씩) 및 1.5초 대기
2. FMP 로고 수집 배치 처리 (10개씩) 및 0.5초 대기
3. limit 파라미터를 사용한 빠른 테스트
4. 예외 처리 강화 확인

사용법:
    python backend/test/test_collection_batch.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).resolve().parent.parent  # backend 디렉토리 (절대경로)
sys.path.insert(0, str(backend_path))

# 로깅 설정 (상세 정보 확인)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_factory
from services.collection_service import (
    collect_and_update_global_top_100,
    fetch_top_100_data,
    fetch_index_tickers,
)


async def test_batch_processing():
    """배치 처리 및 Rate Limit 회피 테스트"""
    print("\n" + "="*70)
    print("🧪 배치 처리 및 Rate Limit 회피 테스트")
    print("="*70)
    
    async with async_session_factory() as db:
        print("\n" + "-"*70)
        print("📋 테스트 옵션:")
        print("   1. 빠른 테스트 (limit=20) - 약 1-2분 소요")
        print("   2. 중간 테스트 (limit=50) - 약 3-5분 소요")
        print("   3. 전체 테스트 (limit=None) - 약 10-15분 소요")
        print("-"*70)
        
        choice = input("\n선택하세요 (1/2/3, 기본값: 1): ").strip()
        
        if choice == "2":
            limit = 50
        elif choice == "3":
            limit = None
        else:
            limit = 20
        
        print(f"\n⏳ 테스트 시작: limit={limit}")
        print("   배치 처리 (20개씩, 배치 간 1.5초 대기)")
        print("   로고 수집 (10개씩, 배치 간 0.5초 대기)")
        print("   예외 처리 강화 확인")
        print("-"*70)
        
        start_time = datetime.now()
        
        try:
            result = await collect_and_update_global_top_100(db, limit=limit)
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            
            print("\n" + "="*70)
            print("✅ 테스트 완료!")
            print("="*70)
            print(f"   소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
            print(f"   수집된 기업 수: {len(result['top_100'])}개")
            
            if result['top_100']:
                print(f"\n📊 상위 5개 기업:")
                for i, item in enumerate(result['top_100'][:5], 1):
                    market_cap = item.get('market_cap_usd', 0)
                    logo = "✅" if item.get('logo_url') else "❌"
                    print(f"   {i}. {item['ticker']} - ${market_cap:,.0f} (로고: {logo})")
                
                # 로고 수집 통계
                logo_count = sum(1 for item in result['top_100'] if item.get('logo_url'))
                print(f"\n🖼️  로고 수집 통계:")
                print(f"   수집 성공: {logo_count}/{len(result['top_100'])}개")
            
            print("\n💡 확인 사항:")
            print("   - 배치 처리 로그에서 '배치 처리: X~Y/총개수' 메시지 확인")
            print("   - 각 배치 사이에 대기 시간이 있는지 확인")
            print("   - 개별 티커 실패가 전체 로직을 중단시키지 않는지 확인")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 테스트 중 오류 발생: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_fetch_top_100_data_directly():
    """fetch_top_100_data 함수 직접 테스트"""
    print("\n" + "="*70)
    print("🧪 fetch_top_100_data 직접 테스트")
    print("="*70)
    
    print("\n⏳ 티커 수집 중...")
    tickers_map = await fetch_index_tickers()
    
    if not tickers_map:
        print("❌ 티커 수집 실패!")
        return False
    
    print(f"✅ {len(tickers_map)}개 티커 수집됨")
    
    # 테스트용으로 30개만 사용
    test_tickers = list(tickers_map.items())[:30]
    test_tickers_map = dict(test_tickers)
    
    print(f"\n⏳ 데이터 수집 시작 (30개 티커)...")
    print("   배치 처리: 20개씩, 배치 간 1.5초 대기")
    
    start_time = datetime.now()
    
    try:
        result = await fetch_top_100_data(test_tickers_map)
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"\n✅ 데이터 수집 완료!")
        print(f"   소요 시간: {elapsed:.1f}초")
        print(f"   유효한 데이터: {len(result)}개")
        
        if result:
            print(f"\n📊 상위 3개:")
            for i, item in enumerate(result[:3], 1):
                print(f"   {i}. {item['ticker']} - ${item.get('market_cap_usd', 0):,.0f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 함수"""
    print("\n" + "="*70)
    print("🚀 배치 처리 및 Rate Limit 회피 테스트")
    print("="*70)
    
    print("\n💡 참고:")
    print("   - 이 테스트는 실제 외부 API(yfinance, FMP)를 호출합니다")
    print("   - Rate Limit을 회피하기 위해 배치 간 대기 시간이 있습니다")
    print("   - 테스트는 시간이 걸릴 수 있습니다")
    
    print("\n" + "-"*70)
    print("테스트 선택:")
    print("   1. 전체 파이프라인 테스트 (collect_and_update_global_top_100)")
    print("   2. fetch_top_100_data 직접 테스트")
    print("-"*70)
    
    choice = input("\n선택하세요 (1/2, 기본값: 1): ").strip()
    
    if choice == "2":
        await test_fetch_top_100_data_directly()
    else:
        await test_batch_processing()
    
    print("\n" + "="*70)
    print("✅ 모든 테스트 완료!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())

