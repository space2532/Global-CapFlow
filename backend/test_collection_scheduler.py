"""
데이터 수집 및 스케줄러 테스트 스크립트

이 스크립트는 다음을 테스트합니다:
1. 뉴스 수집 (뉴스가 없어도 빈 레코드 저장)
2. DB 우선 사용 로직
3. 스케줄러 수동 실행

사용법:
1. FastAPI 서버가 실행 중이어야 합니다:
   uvicorn app.main:app --reload --app-dir backend

2. 이 스크립트를 실행:
   python backend/test_collection_scheduler.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app import models
from app.services.collection_service import (
    collect_news_for_top_100,
    collect_daily_prices,
    collect_and_update_global_top_100,
)
from app.routers.analyze import fetch_ticker_data


async def test_news_collection_with_empty():
    """뉴스가 없어도 빈 레코드가 저장되는지 테스트"""
    print("\n" + "="*60)
    print("📰 테스트 1: 뉴스 수집 (빈 레코드 저장 확인)")
    print("="*60)
    
    async with async_session_factory() as db:
        # 뉴스 수집 실행
        print("\n⏳ 뉴스 수집 중...")
        count = await collect_news_for_top_100(db)
        print(f"✅ 수집 완료: {count}개 기업")
        
        # DB에서 오늘 날짜의 MarketReport 확인
        today = datetime.utcnow().date()
        stmt = select(models.MarketReport).where(
            models.MarketReport.source_type == "daily_news",
            models.MarketReport.collected_at >= datetime.combine(today, datetime.min.time())
        ).order_by(models.MarketReport.collected_at.desc())
        
        result = await db.execute(stmt)
        reports = result.scalars().all()
        
        print(f"\n📊 오늘 수집된 리포트 수: {len(reports)}")
        
        # 빈 레코드 확인
        empty_reports = [r for r in reports if r.raw_data == "No news collected for this date"]
        print(f"📋 뉴스가 없는 기업 수: {len(empty_reports)}")
        
        if empty_reports:
            print("\n✅ 빈 레코드 저장 확인:")
            for report in empty_reports[:3]:  # 최대 3개만 출력
                print(f"   - {report.ticker}: {report.summary_content}")
        
        # 뉴스가 있는 레코드 확인
        news_reports = [r for r in reports if r.raw_data != "No news collected for this date"]
        print(f"\n📰 뉴스가 있는 기업 수: {len(news_reports)}")
        
        if news_reports:
            print("\n✅ 뉴스 데이터 확인:")
            for report in news_reports[:3]:  # 최대 3개만 출력
                print(f"   - {report.ticker}: {report.summary_content[:50]}...")
        
        return len(reports) > 0


async def test_db_priority():
    """DB 우선 사용 로직 테스트"""
    print("\n" + "="*60)
    print("💾 테스트 2: DB 우선 사용 로직")
    print("="*60)
    
    async with async_session_factory() as db:
        # 상위 100개 기업 중 하나 선택
        stmt = select(models.Ranking).where(
            models.Ranking.year == datetime.utcnow().year
        ).order_by(models.Ranking.rank).limit(1)
        
        result = await db.execute(stmt)
        ranking = result.scalar_one_or_none()
        
        if not ranking:
            print("⚠️ 상위 100개 기업 데이터가 없습니다. 먼저 수집을 실행하세요.")
            return False
        
        test_ticker = ranking.ticker
        print(f"\n📌 테스트 티커: {test_ticker}")
        
        # 1. DB에서 데이터 조회
        print("\n1️⃣ DB에서 데이터 조회 중...")
        ticker_data = await fetch_ticker_data(test_ticker, db)
        
        print(f"   - Company 정보: {'있음' if ticker_data.get('company') else '없음'}")
        print(f"   - Financial 데이터: {len(ticker_data.get('financials', []))}개")
        print(f"   - News 데이터: {len(ticker_data.get('news', []))}개")
        
        # News 데이터 형식 확인
        if ticker_data.get('news'):
            news_item = ticker_data['news'][0]
            if isinstance(news_item, dict) and 'raw_data' in news_item:
                print("   ✅ DB에서 가져온 데이터 형식 (raw_data, summary_content 사용)")
            else:
                print("   ⚠️ 외부 API에서 가져온 데이터 형식")
        
        # 2. 최신 MarketReport 확인
        stmt = select(models.MarketReport).where(
            models.MarketReport.ticker == test_ticker,
            models.MarketReport.source_type == "daily_news"
        ).order_by(models.MarketReport.collected_at.desc()).limit(1)
        
        result = await db.execute(stmt)
        latest_report = result.scalar_one_or_none()
        
        if latest_report:
            age_hours = (datetime.utcnow() - latest_report.collected_at).total_seconds() / 3600
            print(f"\n2️⃣ 최신 MarketReport 확인:")
            print(f"   - 수집 시간: {latest_report.collected_at}")
            print(f"   - 경과 시간: {age_hours:.1f}시간")
            print(f"   - 24시간 이내: {'✅ 예' if age_hours < 24 else '❌ 아니오 (외부 API 호출 필요)'}")
            print(f"   - 요약: {latest_report.summary_content[:50] if latest_report.summary_content else 'N/A'}...")
        
        return True


async def test_top_100_collection():
    """상위 100개 기업 수집 테스트"""
    print("\n" + "="*60)
    print("🏆 테스트 3: 상위 100개 기업 수집")
    print("="*60)
    
    async with async_session_factory() as db:
        print("\n⏳ 상위 100개 기업 수집 중... (시간이 걸릴 수 있습니다)")
        result = await collect_and_update_global_top_100(db)
        
        print(f"✅ 수집 완료: {len(result)}개 기업")
        
        # DB에서 Ranking 확인
        current_year = datetime.utcnow().year
        stmt = select(models.Ranking).where(
            models.Ranking.year == current_year
        ).order_by(models.Ranking.rank).limit(10)
        
        result = await db.execute(stmt)
        rankings = result.scalars().all()
        
        print(f"\n📊 상위 10개 기업:")
        for ranking in rankings:
            print(f"   {ranking.rank}. {ranking.ticker} ({ranking.company_name}) - 시가총액: ${ranking.market_cap:,.0f}" if ranking.market_cap else f"   {ranking.rank}. {ranking.ticker} ({ranking.company_name})")
        
        return len(rankings) > 0


async def test_daily_price_collection():
    """일별 주가 수집 테스트"""
    print("\n" + "="*60)
    print("📈 테스트 4: 일별 주가 수집")
    print("="*60)
    
    async with async_session_factory() as db:
        print("\n⏳ 주가 수집 중... (시간이 걸릴 수 있습니다)")
        count = await collect_daily_prices(db)
        
        print(f"✅ 수집 완료: {count}개 기업")
        
        # DB에서 오늘 날짜의 Price 확인
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        stmt = select(models.Price).where(
            models.Price.date >= today_start
        ).limit(10)
        
        result = await db.execute(stmt)
        prices = result.scalars().all()
        
        print(f"\n📊 오늘 수집된 주가 데이터: {len(prices)}개")
        
        if prices:
            print("\n📈 샘플 데이터:")
            for price in prices[:5]:
                print(f"   - {price.ticker}: ${price.close:,.2f}" if price.close else f"   - {price.ticker}: N/A")
        
        return count > 0


async def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("🚀 데이터 수집 및 스케줄러 테스트 시작")
    print("="*60)
    
    print("\n💡 참고:")
    print("   - 이 테스트는 실제 외부 API를 호출합니다")
    print("   - OpenAI API 키가 설정되어 있어야 AI 분석이 작동합니다")
    print("   - 테스트는 시간이 걸릴 수 있습니다")
    
    try:
        # 테스트 1: 뉴스 수집 (빈 레코드 저장)
        await test_news_collection_with_empty()
        
        # 테스트 2: DB 우선 사용
        await test_db_priority()
        
        # 테스트 3: 상위 100개 기업 수집 (선택적)
        print("\n" + "="*60)
        response = input("상위 100개 기업 수집 테스트를 실행하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            await test_top_100_collection()
        
        # 테스트 4: 일별 주가 수집 (선택적)
        print("\n" + "="*60)
        response = input("일별 주가 수집 테스트를 실행하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            await test_daily_price_collection()
        
        print("\n\n" + "="*60)
        print("✅ 테스트 완료!")
        print("="*60)
        print("\n💡 추가 확인 사항:")
        print("   1. DB에서 MarketReport 테이블 확인")
        print("   2. 뉴스가 없는 기업도 레코드가 저장되었는지 확인")
        print("   3. analyze/matchup API 호출 시 DB 데이터가 우선 사용되는지 확인")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
