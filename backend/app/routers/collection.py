from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from app.services.collection_service import collect_and_update_global_top_100


router = APIRouter(
    prefix="/collections",
    tags=["collections"],
)


@router.post("/global-top-100", summary="글로벌 시가총액 상위 100대 기업 수집 및 DB 반영")
async def run_global_top_100_pipeline(db: AsyncSession = Depends(get_db)):
    """
    DuckDuckGo + yfinance를 이용해 글로벌 시가총액 상위 100대 기업을 수집하고
    companies / rankings / prices 테이블에 반영합니다.
    """
    result = await collect_and_update_global_top_100(db)
    return {
        "count": len(result["top_100"]),
        "ranking_date": str(result["ranking_date"]),
        "items": result["top_100"],
        "changes": result["changes"],
    }



