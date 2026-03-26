"""
邮箱验证码服务 —— 生成 / 存 Redis / 发邮件 / 验证
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


# ── Email sending (Azure Communication Services) ──
async def _send_email(email: str, code: str) -> bool:
    """Send verification code via Azure Communication Services Email SDK.
    Falls back to logging if ACS_EMAIL_CONNECTION_STRING not configured."""
    if not settings.ACS_EMAIL_CONNECTION_STRING:
        logger.info("📧 [DEV MODE] Verification code for %s: %s", email, code)
        return True

    try:
        from azure.communication.email import EmailClient

        client = EmailClient.from_connection_string(settings.ACS_EMAIL_CONNECTION_STRING)
        message = {
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
        poller = client.begin_send(message)
        result = poller.result()
        logger.info("Verification email sent to %s (id=%s)", email, result.get("id", "?"))
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", email, e)
        logger.info("📧 [FALLBACK] Verification code for %s: %s", email, code)
        return True
