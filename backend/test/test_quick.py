"""간단한 빠른 테스트"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from app.database import async_session_factory
from app import models
from app.services import stock_service

async def test():
    print("="*60)
    print("🌍 국가 데이터 테스트")
    print("="*60)
    
    # 1. 국가 데이터 수집
    print("\n1. 국가 데이터 수집 중...")
    ticker = "AAPL"
    try:
        stock_data = await stock_service.fetch_company_data(ticker)
        country = stock_data.get("company", {}).get("country")
        print(f"   {ticker} 국가: {country}")
    except Exception as e:
        print(f"   오류: {e}")
    
    # 2. DB 확인
    print("\n2. DB에서 국가 데이터 확인...")
    async with async_session_factory() as db:
        stmt = select(func.count(models.Company.ticker))
        result = await db.execute(stmt)
        total = result.scalar()
        print(f"   전체 기업 수: {total}")
        
        stmt = select(func.count(models.Company.ticker)).where(
            models.Company.country.is_not(None)
        )
        result = await db.execute(stmt)
        with_country = result.scalar()
        print(f"   국가 정보 있음: {with_country}")
    
    # 3. 분기 리포트 확인
    print("\n3. 분기별 리포트 확인...")
    async with async_session_factory() as db:
        stmt = select(func.count(models.QuarterlyReport.id))
        result = await db.execute(stmt)
        count = result.scalar()
        print(f"   전체 리포트 수: {count}")
    
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test())




