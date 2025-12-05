"""
새로 추가된 기능 테스트 스크립트

1. 기업의 국가 데이터 수집 기능 테스트
2. 분기별 리포트 생성 기능 테스트

사용법:
    python backend/test_new_features.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app import models
from app.services import stock_service, collection_service


async def test_country_data_collection():
    """기업의 국가 데이터 수집 기능 테스트"""
    print("\n" + "="*70)
    print("🌍 기업의 국가 데이터 수집 기능 테스트")
    print("="*70)
    
    # 테스트할 티커들 (다양한 국가의 기업)
    test_tickers = ["AAPL", "TSLA", "ASML", "TSM", "SAP"]
    
    print(f"\n📋 테스트 티커: {', '.join(test_tickers)}")
    print("\n⏳ 국가 데이터 수집 중...")
    
    async with async_session_factory() as db:
        for ticker in test_tickers:
            try:
                # stock_service로 데이터 수집
                stock_data = await stock_service.fetch_company_data(ticker)
                company_info = stock_data.get("company", {})
                
                country = company_info.get("country")
                name = company_info.get("name", ticker)
                
                print(f"\n  ✅ {ticker} ({name})")
                print(f"     국가: {country if country else 'N/A'}")
                
                # DB에 저장
                stmt = select(models.Company).where(models.Company.ticker == ticker)
                result = await db.execute(stmt)
                existing_company = result.scalar_one_or_none()
                
                if existing_company:
                    existing_company.country = country or existing_company.country
                    print(f"     DB 업데이트: {existing_company.country}")
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
                    print(f"     DB 저장: {country}")
                
            except Exception as e:
                print(f"\n  ❌ {ticker} 실패: {type(e).__name__}: {e}")
        
        await db.commit()
    
    # DB에서 확인
    print("\n" + "-"*70)
    print("📊 DB에서 국가 데이터 확인:")
    print("-"*70)
    
    async with async_session_factory() as db:
        stmt = select(models.Company).where(
            models.Company.ticker.in_(test_tickers)
        )
        result = await db.execute(stmt)
        companies = result.scalars().all()
        
        for company in companies:
            country_str = company.country if company.country else "N/A"
            print(f"  {company.ticker}: {country_str}")
    
    print("\n✅ 국가 데이터 수집 테스트 완료!")


async def test_quarterly_report_generation():
    """분기별 리포트 생성 기능 테스트"""
    print("\n" + "="*70)
    print("📊 분기별 리포트 생성 기능 테스트")
    print("="*70)
    
    # 현재 분기 계산
    now = datetime.now(timezone.utc)
    current_year = now.year
    current_quarter = (now.month - 1) // 3 + 1
    
    print(f"\n📅 현재 분기: {current_year}년 {current_quarter}분기")
    print("\n💡 참고:")
    print("   - 재무 데이터가 있는 기업에 대해서만 리포트 생성됩니다")
    print("   - 이미 리포트가 있으면 건너뛰기됩니다")
    print("   - OpenAI API 키가 필요합니다")
    
    response = input("\n분기별 리포트 생성을 실행하시겠습니까? (y/n): ").strip().lower()
    
    if response != 'y':
        print("\n⏭️  테스트를 건너뜁니다.")
        return
    
    print("\n⏳ 분기별 리포트 생성 중...")
    print("   (시간이 걸릴 수 있습니다 - 각 기업당 약 5-10초)")
    
    try:
        async with async_session_factory() as db:
            count = await collection_service.collect_quarterly_reports(db)
            
            print(f"\n✅ 리포트 생성 완료: {count}개")
            
            # 생성된 리포트 확인
            print("\n" + "-"*70)
            print("📋 생성된 리포트 확인:")
            print("-"*70)
            
            stmt = select(models.QuarterlyReport).where(
                models.QuarterlyReport.year == current_year,
                models.QuarterlyReport.quarter == current_quarter
            ).order_by(models.QuarterlyReport.created_at.desc()).limit(5)
            
            result = await db.execute(stmt)
            reports = result.scalars().all()
            
            if reports:
                for report in reports:
                    content_preview = report.content[:100] if report.content else "N/A"
                    print(f"\n  📄 {report.ticker} ({report.year}Q{report.quarter})")
                    print(f"     생성 시간: {report.created_at}")
                    print(f"     내용 미리보기: {content_preview}...")
            else:
                print("\n  ⚠️  생성된 리포트가 없습니다.")
                print("     - 재무 데이터가 없거나")
                print("     - 이미 리포트가 존재할 수 있습니다")
    
    except Exception as e:
        print(f"\n❌ 리포트 생성 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def check_country_data_in_db():
    """DB에서 국가 데이터 확인"""
    print("\n" + "="*70)
    print("🔍 DB에서 국가 데이터 확인")
    print("="*70)
    
    async with async_session_factory() as db:
        # 국가별 기업 수 집계
        stmt = select(
            models.Company.country,
            func.count(models.Company.ticker).label("count")
        ).group_by(models.Company.country).order_by(func.count(models.Company.ticker).desc())
        
        result = await db.execute(stmt)
        country_stats = result.all()
        
        print("\n📊 국가별 기업 수:")
        print("-"*70)
        
        total_with_country = 0
        total_without_country = 0
        
        for country, count in country_stats:
            if country:
                print(f"  {country}: {count}개")
                total_with_country += count
            else:
                print(f"  (국가 정보 없음): {count}개")
                total_without_country += count
        
        print("-"*70)
        print(f"  총 기업 수: {total_with_country + total_without_country}개")
        print(f"  국가 정보 있음: {total_with_country}개")
        print(f"  국가 정보 없음: {total_without_country}개")
        
        # 샘플 기업 확인
        print("\n📋 국가 정보가 있는 샘플 기업 (10개):")
        print("-"*70)
        
        stmt = select(models.Company).where(
            models.Company.country.is_not(None)
        ).limit(10)
        
        result = await db.execute(stmt)
        companies = result.scalars().all()
        
        for company in companies:
            print(f"  {company.ticker}: {company.name} ({company.country})")


async def check_quarterly_reports_in_db():
    """DB에서 분기별 리포트 확인"""
    print("\n" + "="*70)
    print("🔍 DB에서 분기별 리포트 확인")
    print("="*70)
    
    async with async_session_factory() as db:
        # 전체 리포트 수
        stmt = select(func.count(models.QuarterlyReport.id))
        result = await db.execute(stmt)
        total_count = result.scalar()
        
        print(f"\n📊 전체 리포트 수: {total_count}")
        
        if total_count == 0:
            print("\n  ⚠️  리포트가 없습니다.")
            print("     분기별 리포트 생성 기능을 실행해보세요.")
            return
        
        # 분기별 리포트 수
        stmt = select(
            models.QuarterlyReport.year,
            models.QuarterlyReport.quarter,
            func.count(models.QuarterlyReport.id).label("count")
        ).group_by(
            models.QuarterlyReport.year,
            models.QuarterlyReport.quarter
        ).order_by(
            desc(models.QuarterlyReport.year),
            desc(models.QuarterlyReport.quarter)
        )
        
        result = await db.execute(stmt)
        quarterly_stats = result.all()
        
        print("\n📊 분기별 리포트 수:")
        print("-"*70)
        for year, quarter, count in quarterly_stats:
            print(f"  {year}년 {quarter}분기: {count}개")
        
        # 최근 리포트 샘플
        print("\n📋 최근 리포트 샘플 (5개):")
        print("-"*70)
        
        stmt = select(models.QuarterlyReport).order_by(
            desc(models.QuarterlyReport.created_at)
        ).limit(5)
        
        result = await db.execute(stmt)
        reports = result.scalars().all()
        
        for report in reports:
            content_preview = report.content[:80] if report.content else "N/A"
            print(f"\n  📄 {report.ticker} ({report.year}Q{report.quarter})")
            print(f"     생성: {report.created_at}")
            print(f"     내용: {content_preview}...")


async def quick_test():
    """빠른 테스트: 국가 데이터만"""
    print("\n" + "="*70)
    print("⚡ 빠른 테스트: 국가 데이터 수집")
    print("="*70)
    
    await test_country_data_collection()
    await check_country_data_in_db()


async def main():
    """메인 테스트 함수"""
    print("\n" + "="*70)
    print("🚀 새로 추가된 기능 테스트")
    print("="*70)
    
    print("\n테스트할 기능을 선택하세요:")
    print("  1. 기업의 국가 데이터 수집 기능 테스트")
    print("  2. 분기별 리포트 생성 기능 테스트")
    print("  3. DB에서 국가 데이터 확인")
    print("  4. DB에서 분기별 리포트 확인")
    print("  5. 모든 테스트 실행")
    print("  6. 빠른 테스트 (국가 데이터만)")
    print("  0. 종료")
    
    try:
        choice = input("\n선택 (0-6): ").strip()
        
        if choice == "0":
            print("\n👋 종료합니다.")
            return
        
        if choice == "1" or choice == "5":
            await test_country_data_collection()
        
        if choice == "2" or choice == "5":
            await test_quarterly_report_generation()
        
        if choice == "3" or choice == "5":
            await check_country_data_in_db()
        
        if choice == "4" or choice == "5":
            await check_quarterly_reports_in_db()
        
        if choice == "6":
            await quick_test()
        
        print("\n" + "="*70)
        print("✅ 테스트 완료!")
        print("="*70)
        print("\n💡 추가 확인 방법:")
        print("   1. DB 데이터 확인: python backend/check_db_data.py")
        print("   2. Supabase 대시보드에서 테이블 직접 확인")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
