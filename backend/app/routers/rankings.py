from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
    - models.Ranking과 models.Company 테이블을 조인하여 sector, industry 정보도 함께 반환
    """
    # Rankings와 Companies 테이블 조인 (N+1 문제 방지)
    stmt = (
        select(
            models.Ranking,
            models.Company
        )
        .join(
            models.Company,
            models.Ranking.ticker == models.Company.ticker,
            isouter=True  # LEFT JOIN: Ranking에 Company가 없어도 포함
        )
        .where(models.Ranking.year == year)
        .order_by(models.Ranking.rank)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No rankings found for year {year}"
        )
    
    # 결과를 RankingRead 스키마로 변환
    rankings = []
    for ranking, company in rows:
        rankings.append(schemas.RankingRead(
            year=ranking.year,
            rank=ranking.rank,
            ticker=ranking.ticker,
            name=company.name if company else ranking.company_name,
            market_cap=ranking.market_cap,
            sector=company.sector if company else None,
            industry=company.industry if company else None,
        ))
    
    return rankings


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
    
    # 3. 해당 티커들의 모든 연도 Ranking 데이터 조회 (Company와 조인하여 name 가져오기)
    stmt_all_rankings = (
        select(
            models.Ranking,
            models.Company
        )
        .join(
            models.Company,
            models.Ranking.ticker == models.Company.ticker,
            isouter=True  # LEFT JOIN
        )
        .where(models.Ranking.ticker.in_(top_tickers))
        .order_by(models.Ranking.ticker, models.Ranking.year)
    )
    
    result = await db.execute(stmt_all_rankings)
    rows = result.all()
    
    # 4. 티커별로 그룹화하여 RankHistoryRead 형태로 변환
    ticker_data = {}
    
    for ranking, company in rows:
        ticker = ranking.ticker
        
        # 티커별 데이터 초기화 (한 번만)
        if ticker not in ticker_data:
            ticker_data[ticker] = {
                "ticker": ticker,
                "name": company.name if company else ranking.company_name,
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
