import asyncio
from collections import Counter
from datetime import date as dt_date
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app import models
from app.database import async_session_factory


async def _get_latest_years(session) -> tuple[int | None, int | None]:
    """랭킹 데이터에서 최신 연도와 직전 연도를 찾습니다."""
    year_stmt = (
        select(models.Ranking.year)
        .distinct()
        .order_by(models.Ranking.year.desc())
        .limit(2)
    )
    result = await session.execute(year_stmt)
    years = [row[0] for row in result.all()]
    latest_year = years[0] if years else None
    previous_year = years[1] if len(years) > 1 else None
    return latest_year, previous_year


async def _fetch_rankings(session, year: int) -> List[models.Ranking]:
    """특정 연도의 랭킹 데이터를 회사 정보와 함께 가져옵니다."""
    stmt = (
        select(models.Ranking)
        .where(models.Ranking.year == year)
        .options(selectinload(models.Ranking.company))
    )
    result = await session.execute(stmt)
    return result.scalars().all()


def _build_dominant_sectors(rankings: List[models.Ranking]) -> List[Dict[str, Any]]:
    """섹터별 비중(%) 목록을 생성합니다."""
    total = len(rankings)
    if total == 0:
        return []
    counter = Counter((r.company.sector if r.company else None) or "Unknown" for r in rankings)
    return [
        {"name": sector, "percentage": round(count / total * 100, 2)}
        for sector, count in counter.most_common()
    ]


def _build_entry_changes(
    latest: List[models.Ranking],
    previous: List[models.Ranking],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """신규 진입/이탈 기업을 계산합니다."""
    latest_map = {r.ticker: {"ticker": r.ticker, "name": r.company_name, "rank": r.rank} for r in latest}
    prev_map = {r.ticker: {"ticker": r.ticker, "name": r.company_name, "rank": r.rank} for r in previous}
    latest_set = set(latest_map.keys())
    prev_set = set(prev_map.keys())

    new_entries = [latest_map[t] for t in sorted(latest_set - prev_set)]
    exited = [prev_map[t] for t in sorted(prev_set - latest_set)]
    return new_entries, exited


async def main():
    async with async_session_factory() as session:
        latest_year, previous_year = await _get_latest_years(session)
        if latest_year is None:
            print("랭킹 데이터가 없습니다.")
            return

        latest_rankings = await _fetch_rankings(session, latest_year)
        previous_rankings: List[models.Ranking] = []
        if previous_year:
            previous_rankings = await _fetch_rankings(session, previous_year)

        dominant_sectors = _build_dominant_sectors(latest_rankings)
        new_entries, exited = _build_entry_changes(latest_rankings, previous_rankings) if previous_rankings else ([], [])

        latest_dates = [r.ranking_date for r in latest_rankings if r.ranking_date]
        trend_date = max(latest_dates) if latest_dates else dt_date(latest_year, 12, 31)

        trend = models.SectorTrend(
            date=trend_date,
            dominant_sectors=dominant_sectors,
            rising_sectors=[],
            new_entries=new_entries,
            exited=exited,
            ai_analysis_text="자동 생성된 트렌드 데이터입니다.",
        )
        session.add(trend)
        await session.commit()
        print("✅ Sector Trend data generated!")


if __name__ == "__main__":
    asyncio.run(main())



