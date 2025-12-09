"""
빠른 테스트: 새로 추가된 기능 간단 테스트

사용법:
    python backend/quick_test_new_features.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, func
from app.database import async_session_factory
from app import models
from app.services import stock_service


async def quick_test():
    """빠른 테스트 실행"""
    print("\n" + "="*70)
    print("⚡ 빠른 테스트: 새로 추가된 기능")
    print("="*70)
    
    # 1. 국가 데이터 수집 테스트 (간단하게 2개만)
    print("\n🌍 1. 국가 데이터 수집 테스트")
    print("-"*70)
    
    test_tickers = ["AAPL", "TSLA"]
    
    async with async_session_factory() as db:
        for ticker in test_tickers:
            try:
                stock_data = await stock_service.fetch_company_data(ticker)
                company_info = stock_data.get("company", {})
                country = company_info.get("country")
                name = company_info.get("name", ticker)
                
                print(f"  ✅ {ticker} ({name}): {country if country else 'N/A'}")
                
                # DB 업데이트
                stmt = select(models.Company).where(models.Company.ticker == ticker)
                result = await db.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    existing.country = country or existing.country
                else:
                    new_company = models.Company(
                        ticker=ticker,
                        name=name,
                        sector=company_info.get("sector"),
                        industry=company_info.get("industry"),
                        country=country,
                        currency=company_info.get("currency"),
                    )
                    db.add(new_company)
            
            except Exception as e:
                print(f"  ❌ {ticker}: {type(e).__name__}: {e}")
        
        await db.commit()
    
    # 2. DB에서 국가 데이터 확인
    print("\n📊 2. DB에서 국가 데이터 확인")
    print("-"*70)
    
    async with async_session_factory() as db:
        stmt = select(
            models.Company.country,
            func.count(models.Company.ticker).label("count")
        ).group_by(models.Company.country).order_by(
            func.count(models.Company.ticker).desc()
        ).limit(5)
        
        result = await db.execute(stmt)
        country_stats = result.all()
        
        print("  국가별 기업 수 (상위 5개):")
        for country, count in country_stats:
            country_name = country if country else "(국가 정보 없음)"
            print(f"    {country_name}: {count}개")
    
    # 3. 분기별 리포트 확인
    print("\n📊 3. 분기별 리포트 확인")
    print("-"*70)
    
    async with async_session_factory() as db:
        stmt = select(func.count(models.QuarterlyReport.id))
        result = await db.execute(stmt)
        total_count = result.scalar()
        
        print(f"  전체 리포트 수: {total_count}개")
        
        if total_count > 0:
            stmt = select(models.QuarterlyReport).order_by(
                models.QuarterlyReport.created_at.desc()
            ).limit(3)
            result = await db.execute(stmt)
            reports = result.scalars().all()
            
            print("  최근 리포트:")
            for report in reports:
                print(f"    - {report.ticker} ({report.year}Q{report.quarter})")
        else:
            print("  ⚠️  리포트가 없습니다. 분기별 리포트 생성 기능을 실행해보세요.")
    
    print("\n" + "="*70)
    print("✅ 빠른 테스트 완료!")
    print("="*70)
    print("\n💡 상세 테스트:")
    print("   python backend/test_new_features.py")


if __name__ == "__main__":
    asyncio.run(quick_test())




