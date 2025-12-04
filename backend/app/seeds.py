"""Seed script to populate initial data in the database."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .create_db import get_async_engine
from . import models  # noqa: F401 - ensure models are imported


# Companies data
COMPANIES_DATA = [
    {"ticker": "AAPL", "name": "Apple Inc.", "industry": "Technology"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "industry": "Technology"},
    {"ticker": "GOOGL", "name": "Alphabet Inc.", "industry": "Technology"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "industry": "Technology"},
    {"ticker": "TSLA", "name": "Tesla, Inc.", "industry": "Technology"},
]

# Financials data (2023, 2024 for each company)
# Values are in millions (USD)
FINANCIALS_DATA = [
    # AAPL
    {
        "ticker": "AAPL",
        "year": 2023,
        "revenue": 383285.0,
        "net_income": 96995.0,
        "per": 31.5,
        "market_cap": 3000000.0,
    },
    {
        "ticker": "AAPL",
        "year": 2024,
        "revenue": 394328.0,
        "net_income": 100903.0,
        "per": 33.2,
        "market_cap": 3200000.0,
    },
    # MSFT
    {
        "ticker": "MSFT",
        "year": 2023,
        "revenue": 211915.0,
        "net_income": 72361.0,
        "per": 35.8,
        "market_cap": 2800000.0,
    },
    {
        "ticker": "MSFT",
        "year": 2024,
        "revenue": 236574.0,
        "net_income": 81200.0,
        "per": 38.5,
        "market_cap": 3100000.0,
    },
    # GOOGL
    {
        "ticker": "GOOGL",
        "year": 2023,
        "revenue": 307394.0,
        "net_income": 73795.0,
        "per": 25.3,
        "market_cap": 1600000.0,
    },
    {
        "ticker": "GOOGL",
        "year": 2024,
        "revenue": 319616.0,
        "net_income": 78220.0,
        "per": 27.1,
        "market_cap": 1800000.0,
    },
    # AMZN
    {
        "ticker": "AMZN",
        "year": 2023,
        "revenue": 574785.0,
        "net_income": 30425.0,
        "per": 58.2,
        "market_cap": 1500000.0,
    },
    {
        "ticker": "AMZN",
        "year": 2024,
        "revenue": 611296.0,
        "net_income": 35200.0,
        "per": 62.5,
        "market_cap": 1700000.0,
    },
    # TSLA
    {
        "ticker": "TSLA",
        "year": 2023,
        "revenue": 96773.0,
        "net_income": 14997.0,
        "per": 45.2,
        "market_cap": 800000.0,
    },
    {
        "ticker": "TSLA",
        "year": 2024,
        "revenue": 108918.0,
        "net_income": 16800.0,
        "per": 48.7,
        "market_cap": 900000.0,
    },
]


async def seed_companies(session: AsyncSession) -> None:
    """Seed companies table with initial data."""
    print("Seeding companies...")
    
    for company_data in COMPANIES_DATA:
        # Check if company already exists
        result = await session.execute(
            select(models.Company).where(models.Company.ticker == company_data["ticker"])
        )
        existing = result.scalar_one_or_none()
        
        if existing is None:
            company = models.Company(**company_data)
            session.add(company)
            print(f"  Added: {company_data['ticker']} - {company_data['name']}")
        else:
            print(f"  Skipped (exists): {company_data['ticker']} - {company_data['name']}")
    
    await session.commit()


async def seed_financials(session: AsyncSession) -> None:
    """Seed financials table with initial data."""
    print("Seeding financials...")
    
    for financial_data in FINANCIALS_DATA:
        # Check if financial record already exists
        result = await session.execute(
            select(models.Financial).where(
                models.Financial.ticker == financial_data["ticker"],
                models.Financial.year == financial_data["year"],
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing is None:
            financial = models.Financial(**financial_data)
            session.add(financial)
            print(
                f"  Added: {financial_data['ticker']} - {financial_data['year']} "
                f"(Revenue: ${financial_data['revenue']:.0f}M)"
            )
        else:
            print(
                f"  Skipped (exists): {financial_data['ticker']} - {financial_data['year']}"
            )
    
    await session.commit()


async def main() -> None:
    """Main function to seed the database."""
    engine = get_async_engine()
    
    try:
        async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session_maker() as session:
            await seed_companies(session)
            await seed_financials(session)
        
        print("\n✅ Seeding completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during seeding: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

