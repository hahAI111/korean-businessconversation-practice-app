"""
Redis 客户端 —— 会话缓存 / 对话上下文 / 限流
支持 REDIS_URL=fake 时使用 fakeredis（本地开发）
Access key 连不上时自动降级为内存缓存，并通过 /api/chat/redis-check 暴露状态
"""

import logging

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client: aioredis.Redis | None = None
_auth_mode: str = "not-connected"  # "access-key" | "fake" | "memory-fallback" | "not-connected"
_last_error: str = ""


def _mask_url(url: str) -> str:
    """Mask credentials in Redis URL for safe logging."""
    if "@" in url:
        prefix, rest = url.rsplit("@", 1)
        return f"{prefix[:15]}...@{rest}"
    return url[:30] + "..."


async def get_redis() -> aioredis.Redis | None:
    """Get Redis client. Returns None if Redis is unavailable (memory fallback active)."""
    global redis_client, _auth_mode, _last_error
    if redis_client is not None:
        return redis_client

    if settings.REDIS_URL == "fake":
        import fakeredis.aioredis
        redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        _auth_mode = "fake"
        logger.info("Redis: using fakeredis (local dev)")
        return redis_client

    masked = _mask_url(settings.REDIS_URL)
    logger.info("Redis: attempting connection to %s", masked)
    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            ssl_cert_reqs=None,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        await client.ping()
        redis_client = client
        _auth_mode = "access-key"
        logger.info("Redis connected (access-key) to %s", masked)
        return redis_client
    except Exception as e:
        _auth_mode = "memory-fallback"
        _last_error = str(e)
        logger.warning("Redis connection failed [%s]: %s — using memory fallback. "
                       "Chat/voice will work but cache is not persistent!", masked, _last_error)
        return None


def get_auth_mode() -> str:
    """Return current Redis auth mode for health check endpoint."""
    return _auth_mode


def get_diagnostics() -> dict:
    """Return Redis diagnostics for health check endpoint."""
    url = settings.REDIS_URL
    info = {
        "auth_mode": _auth_mode,
        "url_scheme": url.split("://")[0] if "://" in url else "unknown",
        "url_masked": _mask_url(url) if url != "fake" else "fake",
    }
    if _last_error:
        info["last_error"] = _last_error
    return info


async def close_redis():
    global redis_client, _auth_mode
    if redis_client:
        await redis_client.close()
        redis_client = None
        _auth_mode = "not-connected"
