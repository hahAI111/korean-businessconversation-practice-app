"""
数据库引擎 —— async SQLAlchemy + PostgreSQL (Azure) / SQLite (本地开发)
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
        "connect_args": {"ssl": _ssl_ctx},
    }

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, **_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话。"""
    async with async_session() as session:
        yield session
