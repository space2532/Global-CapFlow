from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/{year}", response_model=List[schemas.RankingRead], summary="특정 연도의 시가총액 상위 기업 리스트")
async def get_rankings_by_year(
    year: int,
    limit: int = Query(default=100, ge=1, le=1000, description="반환할 상위 기업 수"),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 연도의 시가총액 순위 데이터를 조회합니다.
    
    - year: 조회할 연도
    - limit: 반환할 상위 기업 수 (기본값: 100, 최대: 1000)
    - Relationship을 활용하여 Company 정보를 자동으로 로드합니다.
    """
    # Relationship을 활용하여 Company 정보를 함께 로드 (N+1 문제 방지)
    stmt = (
        select(models.Ranking)
        .options(selectinload(models.Ranking.company))
        .where(models.Ranking.year == year)
        .order_by(models.Ranking.rank)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rankings = result.scalars().all()
    
    if not rankings:
        raise HTTPException(
            status_code=404,
            detail=f"No rankings found for year {year}"
        )
    
    # 결과를 RankingRead 스키마로 변환 (Relationship 활용)
    return [
        schemas.RankingRead(
            year=ranking.year,
            rank=ranking.rank,
            ticker=ranking.ticker,
            name=ranking.company.name if ranking.company else ranking.company_name,
            market_cap=ranking.market_cap,
            sector=ranking.company.sector if ranking.company else None,
            industry=ranking.company.industry if ranking.company else None,
        )
        for ranking in rankings
    ]


@router.get("/history", response_model=List[schemas.RankHistoryRead], summary="상위 기업들의 연도별 순위 변동 데이터")
async def get_rankings_history(
    limit: int = Query(default=10, ge=1, le=100, description="상위 N개 기업 기준"),
    db: AsyncSession = Depends(get_db)
):
    """
    상위 기업들의 연도별 순위 변동 데이터를 조회합니다 (Bump Chart용).
    
    - limit: 상위 N개 기업 기준 (기본값: 10)
    
    로직:
    1. 가장 최신 연도(max(year))를 찾음
    2. 그 연도의 상위 limit개 기업 티커를 추출
    3. 해당 티커들의 모든 연도 Ranking 데이터를 조회
    4. 티커별로 그룹화하여 RankHistoryRead 형태로 변환해서 반환
    """
    # 1. 가장 최신 연도 찾기
    stmt_max_year = select(func.max(models.Ranking.year))
    result = await db.execute(stmt_max_year)
    max_year = result.scalar()
    
    if max_year is None:
        raise HTTPException(
            status_code=404,
            detail="No ranking data found in database"
        )
    
    # 2. 최신 연도의 상위 limit개 기업 티커 추출
    stmt_top_tickers = (
        select(models.Ranking.ticker)
        .where(models.Ranking.year == max_year)
        .order_by(models.Ranking.rank)
        .limit(limit)
    )
    result = await db.execute(stmt_top_tickers)
    top_tickers = [row[0] for row in result.all()]
    
    if not top_tickers:
        return []
    
    # 3. 해당 티커들의 모든 연도 Ranking 데이터 조회 (Relationship 활용)
    stmt_all_rankings = (
        select(models.Ranking)
        .options(selectinload(models.Ranking.company))
        .where(models.Ranking.ticker.in_(top_tickers))
        .order_by(models.Ranking.ticker, models.Ranking.year)
    )
    
    result = await db.execute(stmt_all_rankings)
    rankings = result.scalars().all()
    
    # 4. 티커별로 그룹화하여 RankHistoryRead 형태로 변환 (Relationship 활용)
    ticker_data = {}
    
    for ranking in rankings:
        ticker = ranking.ticker
        
        # 티커별 데이터 초기화 (한 번만)
        if ticker not in ticker_data:
            ticker_data[ticker] = {
                "ticker": ticker,
                "name": ranking.company.name if ranking.company else ranking.company_name,
                "history": []
            }
        
        # RankHistoryItem 추가
        ticker_data[ticker]["history"].append(
            schemas.RankHistoryItem(
                year=ranking.year,
                rank=ranking.rank
            )
        )
    
    # RankHistoryRead 리스트로 변환
    rank_history_list = [
        schemas.RankHistoryRead(
            ticker=data["ticker"],
            name=data["name"],
            history=data["history"]
        )
        for data in ticker_data.values()
    ]
    
    return rank_history_list


@router.get("/movers/latest", response_model=schemas.RankingMoversResponse, summary="최신 연도 신규 진입/이탈 기업")
async def get_latest_movers(db: AsyncSession = Depends(get_db)):
    """
    가장 최근 연도와 그 이전 연도의 Top 100 데이터를 비교하여
    신규 진입(new_entries)과 이탈(exited) 기업을 반환합니다.
    """
    # 최신 연도 조회
    result = await db.execute(select(func.max(models.Ranking.year)))
    latest_year = result.scalar()

    if latest_year is None:
        return schemas.RankingMoversResponse(year=None, new_entries=[], exited=[])

    # 이전 연도 조회
    result_prev = await db.execute(
        select(func.max(models.Ranking.year)).where(models.Ranking.year < latest_year)
    )
    prev_year = result_prev.scalar()

    # 최신 연도 Top 100
    stmt_latest = (
        select(models.Ranking)
        .options(selectinload(models.Ranking.company))
        .where(models.Ranking.year == latest_year)
        .order_by(models.Ranking.rank)
        .limit(100)
    )
    latest_result = await db.execute(stmt_latest)
    latest_rankings = latest_result.scalars().all()
    latest_map = {r.ticker: r for r in latest_rankings}

    prev_map = {}
    if prev_year:
        stmt_prev = (
            select(models.Ranking)
            .options(selectinload(models.Ranking.company))
            .where(models.Ranking.year == prev_year)
            .order_by(models.Ranking.rank)
            .limit(100)
        )
        prev_result = await db.execute(stmt_prev)
        prev_rankings = prev_result.scalars().all()
        prev_map = {r.ticker: r for r in prev_rankings}

    latest_tickers = set(latest_map.keys())
    prev_tickers = set(prev_map.keys())

    new_entries = latest_tickers - prev_tickers
    exited = prev_tickers - latest_tickers

    def _as_mover(item: models.Ranking, is_new: bool, change: int | None) -> schemas.MoverItem:
        company = item.company
        return schemas.MoverItem(
            rank=item.rank,
            ticker=item.ticker,
            name=company.name if company else item.company_name,
            logo_url=company.logo_url if company else None,
            change=change,
            is_new=is_new,
        )

    new_entries_list = [_as_mover(latest_map[t], True, None) for t in sorted(new_entries, key=lambda x: latest_map[x].rank)]

    exited_list = [
        schemas.MoverItem(
            rank=None,
            ticker=prev_map[t].ticker,
            name=prev_map[t].company.name if prev_map[t].company else prev_map[t].company_name,
            logo_url=prev_map[t].company.logo_url if prev_map[t].company else None,
            change=None,
            is_new=False,
        )
        for t in sorted(exited, key=lambda x: prev_map[x].rank)
    ]

    return schemas.RankingMoversResponse(
        year=latest_year,
        new_entries=new_entries_list,
        exited=exited_list,
    )

