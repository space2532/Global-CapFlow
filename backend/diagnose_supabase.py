"""
Supabase 데이터 확인 및 진단 스크립트

Supabase 대시보드에서 데이터를 확인할 수 없는 문제를 진단합니다.

사용법:
    python backend/diagnose_supabase.py
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory, engine
from app import models
from app.config import settings


async def check_table_exists():
    """테이블이 존재하는지 확인"""
    print("\n" + "="*60)
    print("🔍 테이블 존재 여부 확인")
    print("="*60)
    
    async with async_session_factory() as db:
        # PostgreSQL에서 모든 테이블 조회
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        result = await db.execute(query)
        tables = [row[0] for row in result.fetchall()]
        
        print(f"\n📊 Supabase에 존재하는 테이블:")
        for table in tables:
            print(f"   ✅ {table}")
        
        # 필요한 테이블 확인
        required_tables = [
            "companies",
            "market_reports",
            "financials",
            "prices",
            "rankings",
            "ai_analysis"
        ]
        
        print(f"\n📋 필요한 테이블:")
        missing_tables = []
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table} - 존재함")
            else:
                print(f"   ❌ {table} - 없음!")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n⚠️ 누락된 테이블: {', '.join(missing_tables)}")
            print("   해결 방법: python -m app.create_db 실행")
        
        return tables, missing_tables


async def check_market_reports_structure():
    """market_reports 테이블 구조 확인"""
    print("\n" + "="*60)
    print("📰 market_reports 테이블 구조 확인")
    print("="*60)
    
    async with async_session_factory() as db:
        query = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'market_reports'
            ORDER BY ordinal_position;
        """)
        
        result = await db.execute(query)
        columns = result.fetchall()
        
        if not columns:
            print("\n❌ market_reports 테이블이 존재하지 않습니다!")
            return False
        
        print(f"\n📊 market_reports 테이블 컬럼:")
        required_columns = {
            "summary_content": False,
            "raw_data": False,
            "sentiment_score": False,
            "ticker": False,
            "collected_at": False,
            "source_type": False
        }
        
        for col_name, data_type, is_nullable in columns:
            nullable_str = "NULL 허용" if is_nullable == "YES" else "NOT NULL"
            print(f"   - {col_name}: {data_type} ({nullable_str})")
            
            if col_name in required_columns:
                required_columns[col_name] = True
        
        print(f"\n📋 필수 컬럼 확인:")
        missing_columns = []
        for col, exists in required_columns.items():
            if exists:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} - 없음!")
                missing_columns.append(col)
        
        if missing_columns:
            print(f"\n⚠️ 누락된 컬럼: {', '.join(missing_columns)}")
            print("   해결 방법: backend/migrations/add_new_fields.sql 실행")
        
        return len(missing_columns) == 0


async def check_data_count():
    """데이터 개수 확인"""
    print("\n" + "="*60)
    print("📊 데이터 개수 확인")
    print("="*60)
    
    async with async_session_factory() as db:
        # market_reports 데이터 확인
        query = text("SELECT COUNT(*) FROM market_reports")
        result = await db.execute(query)
        count = result.scalar()
        
        print(f"\n📰 market_reports 데이터: {count}개")
        
        if count == 0:
            print("   ⚠️ 데이터가 없습니다!")
            print("   해결 방법:")
            print("   1. 수집 스크립트 실행: python backend/test_collection_scheduler.py")
            print("   2. 또는 API 호출: POST /collections/global-top-100")
        else:
            # 최근 데이터 확인
            query = text("""
                SELECT ticker, collected_at, 
                       CASE 
                           WHEN summary_content IS NULL THEN '요약 없음'
                           WHEN LENGTH(summary_content) = 0 THEN '요약 없음'
                           ELSE '요약 있음'
                       END as has_summary
                FROM market_reports
                ORDER BY collected_at DESC
                LIMIT 5;
            """)
            result = await db.execute(query)
            recent_data = result.fetchall()
            
            print(f"\n📋 최근 5개 데이터:")
            for ticker, collected_at, has_summary in recent_data:
                print(f"   - {ticker}: {collected_at} ({has_summary})")


async def check_database_connection():
    """데이터베이스 연결 확인"""
    print("\n" + "="*60)
    print("🔌 데이터베이스 연결 확인")
    print("="*60)
    
    db_url = settings.database_url
    if "@" in db_url:
        parts = db_url.split("@")
        if "://" in parts[0]:
            user_pass = parts[0].split("://")[1]
            if ":" in user_pass:
                user = user_pass.split(":")[0]
                masked_url = db_url.replace(f":{user_pass.split(':')[1]}", ":****")
            else:
                masked_url = db_url
        else:
            masked_url = db_url
    else:
        masked_url = db_url
    
    print(f"\n📡 연결 정보:")
    print(f"   URL: {masked_url}")
    
    # Supabase인지 확인
    if "supabase" in db_url.lower():
        print("   ✅ Supabase 데이터베이스로 확인됨")
    else:
        print("   ⚠️ Supabase가 아닌 것으로 보입니다")
    
    try:
        async with async_session_factory() as db:
            query = text("SELECT version()")
            result = await db.execute(query)
            version = result.scalar()
            print(f"   ✅ 연결 성공")
            print(f"   PostgreSQL 버전: {version[:50]}...")
            return True
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        return False


async def main():
    """메인 진단 함수"""
    print("\n" + "="*60)
    print("🔍 Supabase 데이터 진단 시작")
    print("="*60)
    
    try:
        # 1. 연결 확인
        connected = await check_database_connection()
        if not connected:
            print("\n❌ 데이터베이스 연결에 실패했습니다.")
            return
        
        # 2. 테이블 존재 확인
        tables, missing_tables = await check_table_exists()
        
        # 3. market_reports 구조 확인
        if "market_reports" in tables:
            structure_ok = await check_market_reports_structure()
        else:
            print("\n❌ market_reports 테이블이 없습니다!")
            structure_ok = False
        
        # 4. 데이터 개수 확인
        if structure_ok:
            await check_data_count()
        
        # 5. 해결 방법 제시
        print("\n\n" + "="*60)
        print("💡 해결 방법")
        print("="*60)
        
        if missing_tables:
            print("\n1️⃣ 테이블 생성:")
            print("   python -m app.create_db")
            print("   또는")
            print("   cd backend && python -m app.create_db")
        
        if not structure_ok and "market_reports" in tables:
            print("\n2️⃣ 테이블 구조 업데이트:")
            print("   Supabase SQL Editor에서 다음 파일 실행:")
            print("   backend/migrations/add_new_fields.sql")
        
        print("\n3️⃣ 데이터 수집:")
        print("   python backend/test_collection_scheduler.py")
        print("   또는")
        print("   API 호출: POST http://localhost:8000/collections/global-top-100")
        
        print("\n4️⃣ Supabase 대시보드에서 확인:")
        print("   - Table Editor > market_reports 테이블 선택")
        print("   - summary_content, raw_data, sentiment_score 컬럼 확인")
        print("   - source_type = 'daily_news' 필터 적용")
        
    except Exception as e:
        print(f"\n❌ 진단 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

