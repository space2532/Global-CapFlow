import asyncio
import sys
from pathlib import Path
from sqlalchemy import text
from app.database import async_session_factory

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

async def check_schema_and_data():
    async with async_session_factory() as db:
        print("\n" + "="*60)
        print("🔍 DB 스키마 및 데이터 상태 점검")
        print("="*60)
        
        # 1. Rankings 테이블 확인
        print("\n[1] Rankings 테이블 점검")
        try:
            # 컬럼 확인
            result = await db.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'rankings';"
            ))
            columns = [row[0] for row in result.fetchall()]
            print(f"   - 컬럼 목록: {', '.join(columns)}")
            
            if 'ranking_date' not in columns:
                print("   ❌ 'ranking_date' 컬럼이 없습니다! (models.py와 DB 불일치)")
            
            # 데이터 수 확인
            result = await db.execute(text("SELECT COUNT(*) FROM rankings"))
            count = result.scalar()
            print(f"   - 전체 행 수: {count}")
            
            # 오늘 날짜 데이터 확인
            result = await db.execute(text("SELECT ranking_date, count(*) FROM rankings GROUP BY ranking_date ORDER BY ranking_date DESC LIMIT 5"))
            rows = result.fetchall()
            if rows:
                print("   - 최근 데이터 현황:")
                for row in rows:
                    print(f"     📅 {row[0]}: {row[1]}개")
            else:
                print("   ⚠️  데이터가 하나도 없습니다.")

        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")

        # 2. Prices 테이블 확인
        print("\n[2] Prices 테이블 점검")
        try:
            result = await db.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'prices';"
            ))
            columns = [row[0] for row in result.fetchall()]
            
            if not columns:
                print("   ❌ Prices 테이블이 존재하지 않습니다!")
            else:
                print(f"   - 컬럼 목록: {', '.join(columns)}")
                result = await db.execute(text("SELECT COUNT(*) FROM prices"))
                count = result.scalar()
                print(f"   - 전체 행 수: {count}")
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_schema_and_data())