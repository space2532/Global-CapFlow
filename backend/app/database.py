from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from .config import settings

# 1. 비동기 엔진 생성
# Supabase Transaction Pooler 및 장기 실행 환경에서의 연결 안정성을 위해
# pool_pre_ping, pool_recycle, connect_args 를 명시적으로 설정한다.
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # 사용 전 연결 유효성 검사로 dead connection 방지
    pool_recycle=300,     # 5분마다 연결 재생성 (ConnectionReset/DoesNotExist 완화)
    # [핵심] Supabase Transaction Pooler(6543 포트) 사용 시 이 설정이 없으면 500 에러 발생
    connect_args={
        "statement_cache_size": 0,  # Supabase Transaction Pooler 필수
        "ssl": "require",           # Supabase에 대한 SSL 연결 강제
    },
)

# 2. 비동기 세션 팩토리 생성
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 3. FastAPI 의존성 주입용 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session