"""
Cache service — Redis wrapper (auto-fallback to in-memory cache when Redis unavailable)
For: conversation context cache, user sessions, learning streaks, hot data
"""

import json
import logging
import time
from typing import Any

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# In-memory fallback when Redis is unavailable
_mem_cache: dict[str, tuple[str, float]] = {}  # key -> (value, expire_timestamp)
_redis_ok = True  # track Redis health


def _mem_get(key: str) -> str | None:
    item = _mem_cache.get(key)
    if item is None:
        return None
    val, exp = item
    if exp and time.time() > exp:
        del _mem_cache[key]
        return None
    return val


def _mem_set(key: str, value: str, ttl: int = 0):
    exp = time.time() + ttl if ttl else 0
    _mem_cache[key] = (value, exp)


class CacheService:

    async def _redis(self):
        """Get Redis client, return None if unavailable."""
        global _redis_ok
        try:
            r = await get_redis()
            if r is None:
                return None
            if not _redis_ok:
                await r.ping()
                _redis_ok = True
                logger.info("Redis reconnected")
            return r
        except Exception:
            if _redis_ok:
                logger.warning("Redis unavailable, using memory fallback")
                _redis_ok = False
            return None

    # ── Conversation thread mapping (user_id → thread_id) ──
    async def get_thread_id(self, user_id: int) -> str | None:
        r = await self._redis()
        if r:
            try:
                return await r.get(f"thread:{user_id}")
            except Exception:
                pass
        return _mem_get(f"thread:{user_id}")

    async def set_thread_id(self, user_id: int, thread_id: str, ttl: int = 86400):
        r = await self._redis()
        if r:
            try:
                await r.set(f"thread:{user_id}", thread_id, ex=ttl)
                return
            except Exception:
                pass
        _mem_set(f"thread:{user_id}", thread_id, ttl)

    async def delete_thread_id(self, user_id: int):
        r = await self._redis()
        if r:
            try:
                await r.delete(f"thread:{user_id}")
                return
            except Exception:
                pass
        _mem_cache.pop(f"thread:{user_id}", None)

    # ── Conversation context summary cache ──
    async def cache_conversation_context(self, thread_id: str, context: dict, ttl: int = 3600):
        r = await self._redis()
        if r:
            try:
                await r.set(f"ctx:{thread_id}", json.dumps(context, ensure_ascii=False), ex=ttl)
                return
            except Exception:
                pass
        _mem_set(f"ctx:{thread_id}", json.dumps(context, ensure_ascii=False), ttl)

    async def get_conversation_context(self, thread_id: str) -> dict | None:
        r = await self._redis()
        if r:
            try:
                data = await r.get(f"ctx:{thread_id}")
                return json.loads(data) if data else None
            except Exception:
                pass
        data = _mem_get(f"ctx:{thread_id}")
        return json.loads(data) if data else None

    # ── Daily study check-in ──
    async def record_study_session(self, user_id: int, minutes: int):
        r = await self._redis()
        if r:
            try:
                key = f"study:{user_id}:today"
                await r.incrby(key, minutes)
                await r.expire(key, 86400)
                return
            except Exception:
                pass
        key = f"study:{user_id}:today"
        cur = int(_mem_get(key) or "0")
        _mem_set(key, str(cur + minutes), 86400)

    async def get_today_study_minutes(self, user_id: int) -> int:
        r = await self._redis()
        if r:
            try:
                val = await r.get(f"study:{user_id}:today")
                return int(val) if val else 0
            except Exception:
                pass
        val = _mem_get(f"study:{user_id}:today")
        return int(val) if val else 0

    # ── Learning streak days ──
    async def get_streak(self, user_id: int) -> int:
        r = await self._redis()
        if r:
            try:
                val = await r.get(f"streak:{user_id}")
                return int(val) if val else 0
            except Exception:
                pass
        val = _mem_get(f"streak:{user_id}")
        return int(val) if val else 0

    async def set_streak(self, user_id: int, days: int, ttl: int = 172800):
        r = await self._redis()
        if r:
            try:
                await r.set(f"streak:{user_id}", days, ex=ttl)
                return
            except Exception:
                pass
        _mem_set(f"streak:{user_id}", str(days), ttl)

    # ── General JSON cache ──
    async def get_json(self, key: str) -> Any:
        r = await self._redis()
        if r:
            try:
                data = await r.get(key)
                return json.loads(data) if data else None
            except Exception:
                pass
        data = _mem_get(key)
        return json.loads(data) if data else None

    async def set_json(self, key: str, value: Any, ttl: int = 3600):
        r = await self._redis()
        if r:
            try:
                await r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
                return
            except Exception:
                pass
        _mem_set(key, json.dumps(value, ensure_ascii=False), ttl)

    # ── API rate limiting ──
    async def check_rate_limit(self, user_id: int, limit: int = 60, window: int = 60) -> bool:
        """Returns True if request is allowed."""
        r = await self._redis()
        if r:
            try:
                key = f"rl:{user_id}"
                count = await r.incr(key)
                if count == 1:
                    await r.expire(key, window)
                return count <= limit
            except Exception:
                pass
        # Memory fallback: simple counter
        key = f"rl:{user_id}"
        val = _mem_get(key)
        count = int(val) + 1 if val else 1
        _mem_set(key, str(count), window)
        return count <= limit


cache_service = CacheService()
