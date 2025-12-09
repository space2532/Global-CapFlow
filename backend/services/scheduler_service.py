import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import async_session_factory
from app.services.collection_service import (
    collect_and_update_global_top_100,
    collect_news_for_top_100,
    collect_daily_prices,
    collect_quarterly_financials,
    collect_quarterly_reports,
)

logger = logging.getLogger(__name__)

# 전역 스케줄러 인스턴스
scheduler: AsyncIOScheduler | None = None


async def scheduled_daily_news_collection() -> None:
    """
    매일 실행되는 뉴스 데이터 수집 작업 함수. (일별)
    """
    logger.info("Starting scheduled daily news collection task...")
    
    try:
        async with async_session_factory() as db:
            count = await collect_news_for_top_100(db)
            logger.info(
                f"Daily news collection completed successfully. "
                f"Collected news for {count} companies."
            )
    except Exception as e:
        logger.error(
            f"Error occurred during scheduled daily news collection: {type(e).__name__}: {e}",
            exc_info=True
        )


async def scheduled_daily_price_collection() -> None:
    """
    매일 실행되는 주가·시가총액·거래량 수집 작업 함수. (일별)
    """
    logger.info("Starting scheduled daily price collection task...")
    
    try:
        async with async_session_factory() as db:
            count = await collect_daily_prices(db)
            logger.info(
                f"Daily price collection completed successfully. "
                f"Collected prices for {count} companies."
            )
    except Exception as e:
        logger.error(
            f"Error occurred during scheduled daily price collection: {type(e).__name__}: {e}",
            exc_info=True
        )


async def scheduled_quarterly_financial_collection() -> None:
    """
    분기별로 실행되는 재무 데이터 수집 작업 함수. (분기별)
    """
    logger.info("Starting scheduled quarterly financial collection task...")
    
    try:
        async with async_session_factory() as db:
            count = await collect_quarterly_financials(db)
            logger.info(
                f"Quarterly financial collection completed successfully. "
                f"Collected financials for {count} companies."
            )
    except Exception as e:
        logger.error(
            f"Error occurred during scheduled quarterly financial collection: {type(e).__name__}: {e}",
            exc_info=True
        )


async def scheduled_quarterly_report_generation() -> None:
    """
    분기별로 실행되는 리포트 생성 작업 함수. (분기별)
    재무 데이터 수집 후 실행되어야 함.
    """
    logger.info("Starting scheduled quarterly report generation task...")
    
    try:
        async with async_session_factory() as db:
            count = await collect_quarterly_reports(db)
            logger.info(
                f"Quarterly report generation completed successfully. "
                f"Generated reports for {count} companies."
            )
    except Exception as e:
        logger.error(
            f"Error occurred during scheduled quarterly report generation: {type(e).__name__}: {e}",
            exc_info=True
        )


async def scheduled_monthly_top_100_collection() -> None:
    """
    매월 실행되는 상위 100개 기업 재조사 작업 함수. (월별)
    """
    logger.info("Starting scheduled monthly top 100 collection task...")
    
    try:
        async with async_session_factory() as db:
            result = await collect_and_update_global_top_100(db)
            logger.info(
                f"Monthly top 100 collection completed successfully. "
                f"Re-evaluated {len(result['top_100'])} companies."
            )
    except Exception as e:
        logger.error(
            f"Error occurred during scheduled monthly top 100 collection: {type(e).__name__}: {e}",
            exc_info=True
        )


def start_scheduler() -> AsyncIOScheduler:
    """
    스케줄러를 시작하고 각 주기별 데이터 수집 작업을 등록합니다.
    
    - 일별: 뉴스 데이터 수집 + 주가·시가총액·거래량 수집 (매일 06:00 KST)
    - 월별: 상위 100개 기업 재조사 (매월 1일 00:00 KST)
    - 분기별: 재무 데이터 수집 (각 분기 말일 18:00 KST)
    
    Returns:
        AsyncIOScheduler: 시작된 스케줄러 인스턴스
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.warning("Scheduler is already running. Skipping start.")
        return scheduler
    
    # AsyncIOScheduler 인스턴스 생성
    scheduler = AsyncIOScheduler()
    
    # 한국 시간대 설정
    kst_timezone = ZoneInfo("Asia/Seoul")
    
    # 1. 일별: 뉴스 데이터 수집 (매일 06:00 KST)
    scheduler.add_job(
        scheduled_daily_news_collection,
        trigger=CronTrigger(hour=6, minute=0, timezone=kst_timezone),
        id="daily_news_collection",
        name="Daily News Collection",
        replace_existing=True,
    )
    
    # 2. 일별: 주가·시가총액·거래량 수집 (매일 06:30 KST - 뉴스 수집 후 실행)
    scheduler.add_job(
        scheduled_daily_price_collection,
        trigger=CronTrigger(hour=6, minute=30, timezone=kst_timezone),
        id="daily_price_collection",
        name="Daily Price Collection",
        replace_existing=True,
    )
    
    # 3. 월별: 상위 100개 기업 재조사 (매월 1일 00:00 KST)
    scheduler.add_job(
        scheduled_monthly_top_100_collection,
        trigger=CronTrigger(day=1, hour=0, minute=0, timezone=kst_timezone),
        id="monthly_top_100_collection",
        name="Monthly Top 100 Collection",
        replace_existing=True,
    )
    
    # 4. 분기별: 재무 데이터 수집 (각 분기 말일 18:00 KST: 3월, 6월, 9월, 12월 마지막 날)
    scheduler.add_job(
        scheduled_quarterly_financial_collection,
        trigger=CronTrigger(month="3,6,9,12", day="last", hour=18, minute=0, timezone=kst_timezone),
        id="quarterly_financial_collection",
        name="Quarterly Financial Collection",
        replace_existing=True,
    )
    
    # 5. 분기별: 리포트 생성 (각 분기 말일 19:00 KST: 재무 데이터 수집 후 실행)
    scheduler.add_job(
        scheduled_quarterly_report_generation,
        trigger=CronTrigger(month="3,6,9,12", day="last", hour=19, minute=0, timezone=kst_timezone),
        id="quarterly_report_generation",
        name="Quarterly Report Generation",
        replace_existing=True,
    )
    
    # 스케줄러 시작
    scheduler.start()
    logger.info(
        "Scheduler started with the following jobs:\n"
        "  - Daily news collection: 06:00 KST\n"
        "  - Daily price collection: 06:30 KST\n"
        "  - Monthly top 100 collection: 1st day of month, 00:00 KST\n"
        "  - Quarterly financial collection: Last day of quarter (Mar/Jun/Sep/Dec), 18:00 KST\n"
        "  - Quarterly report generation: Last day of quarter (Mar/Jun/Sep/Dec), 19:00 KST"
    )
    
    return scheduler


def shutdown_scheduler() -> None:
    """
    스케줄러를 종료합니다.
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown completed.")
        scheduler = None
    else:
        logger.warning("Scheduler is not running. Nothing to shutdown.")
