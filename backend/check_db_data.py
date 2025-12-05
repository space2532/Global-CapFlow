"""
DB 데이터 확인 스크립트

수집하고 요약한 데이터를 DB에서 확인하는 스크립트입니다.

사용법:
    python backend/check_db_data.py
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


async def check_market_reports():
    """MarketReport 테이블 데이터 확인"""
    print("\n" + "="*60)
    print("📰 MarketReport 테이블 (뉴스 요약 데이터)")
    print("="*60)
    
    async with async_session_factory() as db:
        # 전체 리포트 수
        stmt = select(func.count(models.MarketReport.id))
        result = await db.execute(stmt)
        total_count = result.scalar()
        print(f"\n📊 전체 리포트 수: {total_count}")
        
        # 최근 10개 리포트
        stmt = select(models.MarketReport).order_by(
            desc(models.MarketReport.collected_at)
        ).limit(10)
        result = await db.execute(stmt)
        reports = result.scalars().all()
        
        print(f"\n📋 최근 10개 리포트:")
        print("-" * 60)
        for report in reports:
            print(f"\n티커: {report.ticker}")
            print(f"수집 시간: {report.collected_at}")
            print(f"요약: {report.summary_content[:100] if report.summary_content else 'N/A'}...")
            print(f"감성 점수: {report.sentiment_score}")
            print(f"뉴스 있음: {'예' if report.raw_data and report.raw_data != 'No news collected for this date' else '아니오 (빈 레코드)'}")
            print("-" * 60)
        
        # 빈 레코드 수 (정확한 조건으로 확인)
        from sqlalchemy import text
        query = text("""
            SELECT COUNT(*) 
            FROM market_reports 
            WHERE raw_data = 'No news collected for this date'
               OR (raw_data IS NULL AND summary_content = 'No recent news available')
        """)
        result = await db.execute(query)
        empty_count = result.scalar()
        print(f"\n📊 빈 레코드 수 (뉴스 없음): {empty_count}")


async def check_companies():
    """Company 테이블 데이터 확인"""
    print("\n" + "="*60)
    print("🏢 Companies 테이블 (기업 정보)")
    print("="*60)
    
    async with async_session_factory() as db:
        stmt = select(func.count(models.Company.ticker))
        result = await db.execute(stmt)
        total_count = result.scalar()
        print(f"\n📊 전체 기업 수: {total_count}")
        
        # 샘플 10개
        stmt = select(models.Company).limit(10)
        result = await db.execute(stmt)
        companies = result.scalars().all()
        
        print(f"\n📋 샘플 기업 (10개):")
        for company in companies:
            print(f"  - {company.ticker}: {company.name} ({company.sector or 'N/A'})")


async def check_rankings():
    """Ranking 테이블 데이터 확인"""
    print("\n" + "="*60)
    print("🏆 Rankings 테이블 (시가총액 순위)")
    print("="*60)
    
    async with async_session_factory() as db:
        current_year = datetime.now(timezone.utc).year
        
        stmt = select(models.Ranking).where(
            models.Ranking.year == current_year
        ).order_by(models.Ranking.rank).limit(10)
        result = await db.execute(stmt)
        rankings = result.scalars().all()
        
        print(f"\n📊 {current_year}년 상위 10개 기업:")
        for ranking in rankings:
            market_cap_str = f"${ranking.market_cap:,.0f}" if ranking.market_cap else "N/A"
            print(f"  {ranking.rank}. {ranking.ticker} ({ranking.company_name}) - {market_cap_str}")


async def check_financials():
    """Financial 테이블 데이터 확인"""
    print("\n" + "="*60)
    print("💰 Financials 테이블 (재무 데이터)")
    print("="*60)
    
    async with async_session_factory() as db:
        stmt = select(func.count(models.Financial.id))
        result = await db.execute(stmt)
        total_count = result.scalar()
        print(f"\n📊 전체 재무 데이터 수: {total_count}")
        
        # 샘플 5개
        stmt = select(models.Financial).order_by(
            desc(models.Financial.year),
            desc(models.Financial.quarter)
        ).limit(5)
        result = await db.execute(stmt)
        financials = result.scalars().all()
        
        print(f"\n📋 샘플 재무 데이터 (5개):")
        for fin in financials:
            quarter_str = f"Q{fin.quarter}" if fin.quarter else "연간"
            print(f"  - {fin.ticker} ({fin.year} {quarter_str}): 매출 ${fin.revenue:,.0f}" if fin.revenue else f"  - {fin.ticker} ({fin.year} {quarter_str}): 매출 N/A")


async def check_prices():
    """Price 테이블 데이터 확인"""
    print("\n" + "="*60)
    print("📈 Prices 테이블 (주가 데이터)")
    print("="*60)
    
    async with async_session_factory() as db:
        stmt = select(func.count(models.Price.id))
        result = await db.execute(stmt)
        total_count = result.scalar()
        print(f"\n📊 전체 주가 데이터 수: {total_count}")
        
        # 최근 5개
        stmt = select(models.Price).order_by(
            desc(models.Price.date)
        ).limit(5)
        result = await db.execute(stmt)
        prices = result.scalars().all()
        
        print(f"\n📋 최근 주가 데이터 (5개):")
        for price in prices:
            price_str = f"${price.close:,.2f}" if price.close else "N/A"
            print(f"  - {price.ticker} ({price.date.date()}): {price_str}")


async def check_ai_analysis():
    """AIAnalysis 테이블 데이터 확인"""
    print("\n" + "="*60)
    print("🤖 AIAnalysis 테이블 (AI 분석 캐시)")
    print("="*60)
    
    async with async_session_factory() as db:
        stmt = select(func.count(models.AIAnalysis.id))
        result = await db.execute(stmt)
        total_count = result.scalar()
        print(f"\n📊 전체 AI 분석 캐시 수: {total_count}")
        
        # 최근 5개
        stmt = select(models.AIAnalysis).order_by(
            desc(models.AIAnalysis.created_at)
        ).limit(5)
        result = await db.execute(stmt)
        analyses = result.scalars().all()
        
        print(f"\n📋 최근 AI 분석 (5개):")
        for analysis in analyses:
            response = analysis.response_json
            if isinstance(response, dict):
                winner = response.get("winner", "N/A")
                print(f"  - {analysis.request_hash[:16]}...: 승자={winner}, 생성={analysis.created_at}")


async def main():
    """메인 함수"""
    print("\n" + "="*60)
    print("🔍 DB 데이터 확인")
    print("="*60)
    
    try:
        await check_market_reports()
        await check_companies()
        await check_rankings()
        await check_financials()
        await check_prices()
        await check_ai_analysis()
        
        print("\n\n" + "="*60)
        print("✅ 데이터 확인 완료!")
        print("="*60)
        print("\n💡 Supabase에서 확인하는 방법:")
        print("   1. Supabase 대시보드 접속")
        print("   2. Table Editor 메뉴 선택")
        print("   3. 다음 테이블 확인:")
        print("      - market_reports: 뉴스 요약 데이터")
        print("      - companies: 기업 정보")
        print("      - rankings: 시가총액 순위")
        print("      - financials: 재무 데이터")
        print("      - prices: 주가 데이터")
        print("      - ai_analysis: AI 분석 캐시")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

