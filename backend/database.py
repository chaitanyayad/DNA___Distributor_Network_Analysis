import asyncpg
from typing import AsyncGenerator
from backend.config import get_settings

# Module-level pool — created once on startup, shared across all requests
_pool: asyncpg.Pool | None = None


async def create_pool() -> None:
    """
    Called once on application startup (registered in main.py lifespan).
    Strips the '+asyncpg' dialect prefix that SQLAlchemy needs but asyncpg
    does not accept in its own connect string.
    """
    global _pool
    settings = get_settings()

    # asyncpg expects 'postgresql://' not 'postgresql+asyncpg://'
    raw_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    _pool = await asyncpg.create_pool(
        dsn=raw_url,
        min_size=2,
        max_size=10,
        command_timeout=60,
    )


async def close_pool() -> None:
    """Called once on application shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """
    FastAPI dependency — yields one connection from the pool per request.
    The connection is automatically returned to the pool after the request
    completes, even if an exception was raised.

    Usage in a route:
        async def my_route(db: asyncpg.Connection = Depends(get_db)):
    """
    if _pool is None:
        raise RuntimeError("Database pool has not been initialised. Check startup.")
    async with _pool.acquire() as connection:
        yield connection