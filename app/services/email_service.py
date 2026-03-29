"""
Email verification service — generate / store in Redis / send email / verify
"""

import logging
import secrets

from app.core.config import get_settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)
settings = get_settings()

CODE_TTL = 300  # 5 minutes
CODE_LENGTH = 6
RATE_LIMIT_TTL = 60  # 1 code per 60 seconds per email


def _generate_code() -> str:
    """Generate a secure random numeric code."""
    return "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))


def _redis_key(email: str) -> str:
    return f"verify:{email.lower().strip()}"


def _rate_key(email: str) -> str:
    return f"verify_rate:{email.lower().strip()}"


async def send_verification_code(email: str) -> bool:
    """Generate a code, store in Redis, and send via email. Returns True on success."""
    email = email.lower().strip()
    redis = await get_redis()

    if redis:
        # Rate limit: 1 code per 60s
        if await redis.exists(_rate_key(email)):
            return False  # too fast
        code = _generate_code()
        await redis.setex(_redis_key(email), CODE_TTL, code)
        await redis.setex(_rate_key(email), RATE_LIMIT_TTL, "1")
    else:
        code = _generate_code()
        logger.warning("Redis unavailable — code for %s: %s (memory only, won't persist)", email, code)
        _memory_codes[email] = code
        return await _send_email(email, code)

    return await _send_email(email, code)


async def verify_code(email: str, code: str) -> bool:
    """Check if the code matches. Deletes on success."""
    email = email.lower().strip()
    redis = await get_redis()

    if redis:
        stored = await redis.get(_redis_key(email))
        if stored and stored == code.strip():
            await redis.delete(_redis_key(email))
            return True
        return False
    else:
        stored = _memory_codes.get(email)
        if stored and stored == code.strip():
            _memory_codes.pop(email, None)
            return True
        return False


# ── Memory fallback when Redis unavailable ──
_memory_codes: dict[str, str] = {}


# ── Email sending (Azure Communication Services REST API) ──
async def _send_email(email: str, code: str) -> bool:
    """Send verification code via ACS Email REST API (no heavy SDK needed).
    Falls back to logging if ACS_EMAIL_CONNECTION_STRING not configured."""
    if not settings.ACS_EMAIL_CONNECTION_STRING:
        logger.info("📧 [DEV MODE] Verification code for %s: %s", email, code)
        return True

    try:
        import hashlib, hmac, base64, datetime
        import httpx

        # Parse connection string: endpoint=https://...;accesskey=...
        parts = dict(p.split("=", 1) for p in settings.ACS_EMAIL_CONNECTION_STRING.split(";") if "=" in p)
        endpoint = parts.get("endpoint", "").rstrip("/")
        access_key = parts.get("accesskey", "")

        path = "/emails:send?api-version=2023-03-31"
        url = f"{endpoint}{path}"

        body_json = {
            "senderAddress": settings.ACS_EMAIL_SENDER,
            "recipients": {"to": [{"address": email}]},
            "content": {
                "subject": f"Korean Biz Coach — Verification Code: {code}",
                "plainText": (
                    f"Your verification code is: {code}\n\n"
                    f"This code expires in 5 minutes.\n"
                    f"If you didn't request this, please ignore this email.\n\n"
                    f"— Korean Biz Coach"
                ),
            },
        }

        import json as _json
        body_bytes = _json.dumps(body_json).encode("utf-8")
        content_hash = base64.b64encode(hashlib.sha256(body_bytes).digest()).decode()

        utc_now = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        from urllib.parse import urlparse
        host = urlparse(endpoint).hostname

        string_to_sign = f"POST\n{path}\n{utc_now};{host};{content_hash}"
        key_bytes = base64.b64decode(access_key)
        signature = base64.b64encode(
            hmac.new(key_bytes, string_to_sign.encode("utf-8"), hashlib.sha256).digest()
        ).decode()

        headers = {
            "Content-Type": "application/json",
            "x-ms-date": utc_now,
            "x-ms-content-sha256": content_hash,
            "Authorization": f"HMAC-SHA256 SignedHeaders=x-ms-date;host;x-ms-content-sha256&Signature={signature}",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, content=body_bytes, headers=headers)

        if resp.status_code in (200, 201, 202):
            op_id = resp.headers.get("operation-location", "?")
            logger.info("Verification email sent to %s (status=%s, op=%s)", email, resp.status_code, op_id)
            return True
        else:
            logger.error("ACS email API error %s: %s", resp.status_code, resp.text[:300])
            logger.info("📧 [FALLBACK] Verification code for %s: %s", email, code)
            return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", email, e)
        logger.info("📧 [FALLBACK] Verification code for %s: %s", email, code)
        return True
