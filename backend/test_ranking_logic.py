import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app import models
from app.services.collection_service import _calculate_ranking_changes


@pytest.fixture
async def async_session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_sessionmaker = sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    try:
        async with async_sessionmaker() as session:
            yield session
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_calculate_ranking_changes_detects_new_entries_and_exits(async_session: AsyncSession):
    prev_date = date(2024, 11, 30)
    async_session.add_all(
        [
            models.Ranking(
                year=2024,
                ranking_date=prev_date,
                rank=1,
                ticker="AAA",
                market_cap=100.0,
                company_name="AAA",
            ),
            models.Ranking(
                year=2024,
                ranking_date=prev_date,
                rank=2,
                ticker="BBB",
                market_cap=90.0,
                company_name="BBB",
            ),
        ]
    )
    await async_session.commit()

    current_top = [
        {"ticker": "AAA", "sector": "Tech"},
        {"ticker": "CCC", "sector": "Finance"},
        {"ticker": "DDD", "sector": None},
    ]

    changes = await _calculate_ranking_changes(
        async_session,
        current_top,
        date(2024, 12, 31),
    )

    assert changes["previous_ranking_date"] == prev_date
    assert changes["new_entries"] == ["CCC", "DDD"]
    assert changes["exited"] == ["BBB"]
    assert changes["sector_stats"] == {"Tech": 1, "Finance": 1, "Unknown": 1}


@pytest.mark.asyncio
async def test_calculate_ranking_changes_without_history(async_session: AsyncSession):
    current_top = [
        {"ticker": "AAA", "sector": "Health"},
        {"ticker": "BBB", "sector": None},
    ]

    changes = await _calculate_ranking_changes(
        async_session,
        current_top,
        date(2024, 12, 31),
    )

    assert set(changes["new_entries"]) == {"AAA", "BBB"}
    assert changes["exited"] == []
    assert changes["sector_stats"]["Health"] == 1
    assert changes["sector_stats"]["Unknown"] == 1
    assert changes["previous_ranking_date"] is None

