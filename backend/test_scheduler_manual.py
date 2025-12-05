"""
스케줄러 작업 수동 실행 테스트 스크립트

이 스크립트는 스케줄러의 각 작업을 지금 당장 수동으로 실행하여 테스트합니다.
실제 스케줄 시간을 기다리지 않고 바로 테스트할 수 있습니다.

사용법:
    python backend/test_scheduler_manual.py
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.scheduler_service import (
    scheduled_daily_news_collection,
    scheduled_daily_price_collection,
    scheduled_monthly_top_100_collection,
    scheduled_quarterly_financial_collection,
)


async def test_all_scheduled_jobs():
    """모든 스케줄된 작업을 순차적으로 실행"""
    print("\n" + "="*70)
    print("🚀 스케줄러 작업 수동 실행 테스트")
    print("="*70)
    
    print("\n💡 참고:")
    print("   - 이 테스트는 실제 외부 API를 호출합니다")
    print("   - OpenAI API 키가 설정되어 있어야 AI 분석이 작동합니다")
    print("   - 각 작업은 시간이 걸릴 수 있습니다")
    print("   - 작업은 순차적으로 실행됩니다")
    
    jobs = [
        ("📰 일별 뉴스 수집", scheduled_daily_news_collection),
        ("📈 일별 주가 수집", scheduled_daily_price_collection),
        ("🏆 월별 상위 100개 기업 재조사", scheduled_monthly_top_100_collection),
        ("💰 분기별 재무 데이터 수집", scheduled_quarterly_financial_collection),
    ]
    
    print("\n" + "="*70)
    print("실행할 작업을 선택하세요:")
    print("="*70)
    for idx, (name, _) in enumerate(jobs, 1):
        print(f"  {idx}. {name}")
    print("  5. 모든 작업 실행")
    print("  0. 종료")
    
    try:
        choice = input("\n선택 (0-5): ").strip()
        
        if choice == "0":
            print("\n👋 종료합니다.")
            return
        
        selected_jobs = []
        if choice == "5":
            selected_jobs = jobs
        elif choice in ["1", "2", "3", "4"]:
            idx = int(choice) - 1
            selected_jobs = [jobs[idx]]
        else:
            print("\n❌ 잘못된 선택입니다.")
            return
        
        # 선택된 작업 실행
        for idx, (name, job_func) in enumerate(selected_jobs, 1):
            print("\n" + "="*70)
            print(f"작업 {idx}/{len(selected_jobs)}: {name}")
            print("="*70)
            
            try:
                print(f"\n⏳ {name} 시작...")
                await job_func()
                print(f"✅ {name} 완료!")
                
            except Exception as e:
                print(f"\n❌ {name} 실패: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
            
            # 작업 간 대기 (선택적)
            if idx < len(selected_jobs):
                print(f"\n⏸️  다음 작업 전 3초 대기...")
                await asyncio.sleep(3)
        
        print("\n" + "="*70)
        print("✅ 모든 작업 완료!")
        print("="*70)
        print("\n💡 다음 단계:")
        print("   1. DB에서 수집된 데이터 확인: python backend/check_db_data.py")
        print("   2. Supabase 대시보드에서 테이블 확인")
        print("   3. 백엔드 서버 실행하여 스케줄러 자동 실행 확인")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


async def quick_test():
    """빠른 테스트: 뉴스 수집만 실행"""
    print("\n" + "="*70)
    print("⚡ 빠른 테스트: 일별 뉴스 수집만 실행")
    print("="*70)
    
    try:
        print("\n⏳ 뉴스 수집 시작...")
        await scheduled_daily_news_collection()
        print("\n✅ 뉴스 수집 완료!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # 명령줄 인자로 빠른 테스트 옵션 제공
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(quick_test())
    else:
        asyncio.run(test_all_scheduled_jobs())
