"""
认证 API —— 注册（含邮箱验证码） / 登录 / Microsoft 登录
"""

import logging

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.core.auth import create_access_token, get_current_user_id, validate_microsoft_id_token
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    MicrosoftAuthRequest,
    SendCodeRequest,
    TokenResponse,
    UserLogin,
    UserProfile,
    UserRegister,
)
from app.services.email_service import send_verification_code, verify_code

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/send-code")
async def send_code(body: SendCodeRequest, db: AsyncSession = Depends(get_db)):
    """发送邮箱验证码（注册前调用）"""
    # Check if email already registered
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    ok = await send_verification_code(body.email)
    if not ok:
        raise HTTPException(status_code=429, detail="Please wait 60 seconds before requesting a new code")
    return {"message": "Verification code sent"}


@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Verify the code
    if not await verify_code(body.email, body.verification_code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user = User(
        email=body.email,
        hashed_password=hashed,
        nickname=body.nickname,
        korean_level=body.korean_level,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.email == body.email))
    except Exception as e:
        logger.error("Database error during login: %s", e)
        raise HTTPException(status_code=503, detail="Database unavailable, please try again later")
    user = result.scalar_one_or_none()
    if not user or not bcrypt.checkpw(body.password.encode(), user.hashed_password.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id)


@router.post("/microsoft", response_model=TokenResponse)
async def microsoft_login(body: MicrosoftAuthRequest, db: AsyncSession = Depends(get_db)):
    """Microsoft Entra ID 登录 — 验证 Microsoft ID token，自动注册/登录"""
    claims = await validate_microsoft_id_token(body.id_token)

    email = claims.get("preferred_username") or claims.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="No email in Microsoft token")

    # Find existing user by email, or create new one
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        nickname = claims.get("name", email.split("@")[0])
        user = User(
            email=email,
            hashed_password="",  # Microsoft-only account, no password
            nickname=nickname,
            korean_level="beginner",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user_id=user.id)


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
