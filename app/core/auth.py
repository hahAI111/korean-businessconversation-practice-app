"""
JWT auth utilities — dual-track: self-signed HS256 + Microsoft Entra ID RS256
"""

import time
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

# ── Microsoft JWKS cache ──
_ms_jwks_cache: dict = {}
_ms_jwks_expires: float = 0


async def _get_microsoft_signing_keys() -> dict[str, jwt.PyJWK]:
    """Fetch and cache Microsoft's JWKS for token validation."""
    global _ms_jwks_cache, _ms_jwks_expires
    if _ms_jwks_cache and time.time() < _ms_jwks_expires:
        return _ms_jwks_cache

    jwks_url = (
        f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}"
        "/discovery/v2.0/keys"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(jwks_url, timeout=10)
        resp.raise_for_status()
    jwks_data = resp.json()
    jwk_set = jwt.PyJWKSet.from_dict(jwks_data)
    _ms_jwks_cache = {k.key_id: k for k in jwk_set.keys}
    _ms_jwks_expires = time.time() + 3600  # cache 1h
    return _ms_jwks_cache


async def validate_microsoft_id_token(id_token: str) -> dict:
    """
    Validate a Microsoft ID token and return claims.
    Raises HTTPException on failure.
    """
    if not settings.ENTRA_TENANT_ID or not settings.ENTRA_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Microsoft login not configured")

    try:
        header = jwt.get_unverified_header(id_token)
        keys = await _get_microsoft_signing_keys()
        key = keys.get(header.get("kid", ""))
        if not key:
            # Refresh cache and retry
            global _ms_jwks_expires
            _ms_jwks_expires = 0
            keys = await _get_microsoft_signing_keys()
            key = keys.get(header.get("kid", ""))
            if not key:
                raise HTTPException(status_code=401, detail="Unknown signing key")

        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=settings.ENTRA_CLIENT_ID,
            issuer=f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/v2.0",
        )
        return claims
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Microsoft token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Microsoft token: {e}")


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _verify_token(token: str) -> int | None:
    """JWT 토큰 검증 — WebSocket 등 Depends 없이 직접 호출용. 실패 시 None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    user_id = _verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id
