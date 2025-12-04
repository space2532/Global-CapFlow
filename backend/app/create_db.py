from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

from .config import settings
from . import models  # noqa: F401  - ensure models are imported so tables are registered


def get_async_engine() -> AsyncEngine:
    """Create an async SQLAlchemy engine using the configured database URL.

    The URL should be an asyncpg-compatible DSN, e.g.:
    postgresql+asyncpg://user:password@host:port/dbname
    """
    return create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        # Connection pool settings for better reliability
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before using
        # Connection timeout (30 seconds)
        connect_args={
            "server_settings": {
                "application_name": "global_capflow_create_db",
            },
            "command_timeout": 30,
            "statement_cache_size": 0,  # Disable prepared statement cache for pgbouncer compatibility
        },
    )


async def init_db(drop_existing: bool = True) -> None:
    """Create all tables defined in SQLModel metadata using an async engine.
    
    Args:
        drop_existing: If True, drop all existing tables before creating new ones.
                      Defaults to True for clean recreation.
    """
    engine = get_async_engine()

    async with engine.begin() as conn:
        if drop_existing:
            print("Dropping existing tables...")
            # Run the synchronous metadata.drop_all in the async context
            await conn.run_sync(SQLModel.metadata.drop_all)
            print("Existing tables dropped.")
        
        print("Creating tables...")
        # Run the synchronous metadata.create_all in the async context
        await conn.run_sync(SQLModel.metadata.create_all)
        print("Tables created successfully.")

    await engine.dispose()


async def main() -> None:
    # Print connection info (without password)
    db_url = settings.database_url
    if "@" in db_url:
        # Mask password in URL for display
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
    
    print(f"Connecting to database: {masked_url}")
    
    try:
        await init_db(drop_existing=True)
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"\n❌ Error: {error_type}: {error_msg}")
        
        print("\nTroubleshooting:")
        if "getaddrinfo" in error_msg.lower() or "gaierror" in error_type.lower():
            print("1. DNS resolution failed - check your internet connection")
            print("2. Verify the hostname in DATABASE_URL is correct")
            print("3. Check if you can access the database host from your network")
            print("4. For Supabase: Ensure your IP is allowed in Supabase dashboard")
            print("5. Try using a VPN or different network if behind firewall")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            print("1. Check if PostgreSQL server is running and accessible")
            print("2. Verify firewall rules allow connection to port 5432")
            print("3. For Supabase: Check connection pooling settings")
            print("4. Try increasing connection timeout")
        else:
            print("1. Make sure PostgreSQL server is running")
            print("2. Check if the database exists")
            print("3. Verify connection details in .env or config.py")
            print("4. Check database credentials (username/password)")
        
        print(f"\nFull error details:")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())



