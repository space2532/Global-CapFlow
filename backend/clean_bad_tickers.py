"""
잘못 수집된 티커 정리 스크립트

날짜 형식 등 잘못된 티커를 DB에서 삭제합니다.
companies 테이블에서 삭제하면 CASCADE 설정에 의해 
rankings, prices, financials 등 연관 데이터도 자동 삭제됩니다.

사용법:
    python backend/clean_bad_tickers.py
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app import models


def is_bad_ticker(ticker: str) -> bool:
    """
    티커가 잘못된 형식인지 검사합니다.
    
    삭제 조건:
    1. 공백(" ")이 포함된 경우
    2. 길이가 8글자 이상인 경우
    3. 숫자로만 구성된 4자리 연도인 경우
    """
    if not ticker:
        return True
    
    # 1. 공백이 포함된 경우
    if " " in ticker:
        return True
    
    # 2. 길이가 8글자 이상인 경우
    if len(ticker) >= 8:
        return True
    
    # 3. 숫자로만 구성된 4자리 연도인 경우
    if ticker.isdigit() and len(ticker) == 4:
        return True
    
    # 접미사 제거 후 검증 (예: "AAPL.T" -> "AAPL")
    if "." in ticker:
        ticker_without_suffix = ticker.split(".")[0]
        # 접미사 제거 후에도 길이가 8글자 이상이면 제외
        if len(ticker_without_suffix) >= 8:
            return True
        # 접미사 제거 후 숫자로만 구성된 4자리면 제외
        if ticker_without_suffix.isdigit() and len(ticker_without_suffix) == 4:
            return True
    
    return False


async def clean_bad_tickers() -> None:
    """잘못된 티커를 DB에서 삭제합니다."""
    print("\n" + "="*70)
    print("🧹 잘못 수집된 티커 정리 스크립트")
    print("="*70)
    
    print("\n💡 삭제 조건:")
    print("   1. 티커에 공백(' ')이 포함된 경우")
    print("   2. 티커 길이가 8글자 이상인 경우")
    print("   3. 티커가 숫자로만 구성된 4자리 연도인 경우")
    print("\n⚠️  주의: companies 테이블에서 삭제하면 CASCADE로")
    print("   rankings, prices, financials 등 연관 데이터도 자동 삭제됩니다.")
    
    async with async_session_factory() as db:
        # 1. 모든 티커 조회
        stmt = select(models.Company.ticker)
        result = await db.execute(stmt)
        all_tickers = [row[0] for row in result.all()]
        
        print(f"\n📊 전체 티커 수: {len(all_tickers)}")
        
        # 2. 잘못된 티커 필터링
        bad_tickers = []
        for ticker in all_tickers:
            if is_bad_ticker(ticker):
                bad_tickers.append(ticker)
        
        if not bad_tickers:
            print("\n✅ 잘못된 티커가 없습니다. 정리할 데이터가 없습니다.")
            return
        
        print(f"\n🔍 발견된 잘못된 티커: {len(bad_tickers)}개")
        print("\n📋 삭제될 티커 목록:")
        print("-" * 70)
        for idx, ticker in enumerate(bad_tickers, 1):
            reason = []
            if " " in ticker:
                reason.append("공백 포함")
            if len(ticker) >= 8:
                reason.append(f"길이 {len(ticker)}자")
            if ticker.isdigit() and len(ticker) == 4:
                reason.append("4자리 연도")
            reason_str = ", ".join(reason) if reason else "기타"
            print(f"  {idx:3d}. {ticker:20s} (이유: {reason_str})")
        
        # 3. 사용자 확인
        print("\n" + "="*70)
        response = input(f"\n⚠️  위 {len(bad_tickers)}개 티커를 삭제하시겠습니까? (yes/no): ")
        
        if response.lower() not in ["yes", "y"]:
            print("\n❌ 삭제가 취소되었습니다.")
            return
        
        # 4. 삭제 실행
        print("\n⏳ 삭제 중...")
        try:
            # 각 티커를 순차적으로 삭제
            deleted_count = 0
            for ticker in bad_tickers:
                try:
                    stmt = delete(models.Company).where(models.Company.ticker == ticker)
                    result = await db.execute(stmt)
                    if result.rowcount > 0:
                        deleted_count += 1
                except Exception as e:
                    print(f"   ⚠️  티커 '{ticker}' 삭제 실패: {e}")
                    continue
            
            # 커밋
            await db.commit()
            
            print(f"\n✅ 삭제 완료: {deleted_count}개 티커가 삭제되었습니다.")
            
            # 5. 삭제 후 확인
            stmt = select(func.count(models.Company.ticker))
            result = await db.execute(stmt)
            remaining_count = result.scalar()
            print(f"📊 남은 티커 수: {remaining_count}개")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ 삭제 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            raise


async def main():
    """메인 함수"""
    try:
        await clean_bad_tickers()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
