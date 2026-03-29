"""
Database engine — async SQLAlchemy + PostgreSQL (Azure) / SQLite (local dev)
"""

import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

_is_postgres = "postgres" in settings.DATABASE_URL
_kwargs: dict = {}

if _is_postgres:
    # Azure PostgreSQL requires SSL
    _ssl_ctx = ssl.create_default_context()
    _kwargs = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 10,
        "pool_pre_ping": True,
        "connect_args": {"ssl": _ssl_ctx, "timeout": 10},
    }

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, **_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency injection: get database session."""
    async with async_session() as session:
        yield session
