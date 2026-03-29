"""
内部管理 API —— 用户统计 / 活跃度 / 内容分析
仅管理员访问（通过 ADMIN_SECRET header 鉴权）
"""

import logging
from datetime import datetime, timedelta, timezone

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Header
from sqlalchemy import func, or_, select, and_, distinct, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import (
    User, Conversation, VocabBook, StudyStreak, KoreanLevel,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ── Admin 鉴权 ──
ADMIN_SECRET = settings.ADMIN_SECRET

async def verify_admin(x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin key")


# ══════════════════════════════════════════════════════════
# 1. 总览仪表盘
# ══════════════════════════════════════════════════════════

@router.get("/overview", dependencies=[Depends(verify_admin)])
async def overview(db: AsyncSession = Depends(get_db)):
    """核心指标一览"""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # 总注册用户
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0

    # 今日新注册
    today_signups = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= today)
    )).scalar() or 0

    # 7天新注册
    week_signups = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )).scalar() or 0

    # 30天新注册
    month_signups = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= month_ago)
    )).scalar() or 0

    # DAU (今天有学习记录的用户)
    dau = (await db.execute(
        select(func.count(distinct(StudyStreak.user_id))).where(StudyStreak.date >= today)
    )).scalar() or 0

    # WAU (7天内有学习记录)
    wau = (await db.execute(
        select(func.count(distinct(StudyStreak.user_id))).where(StudyStreak.date >= week_ago)
    )).scalar() or 0

    # MAU (30天内有学习记录)
    mau = (await db.execute(
        select(func.count(distinct(StudyStreak.user_id))).where(StudyStreak.date >= month_ago)
    )).scalar() or 0

    # 总对话数 / 总词汇数
    total_conversations = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    total_vocab = (await db.execute(select(func.count(VocabBook.id)))).scalar() or 0
    mastered_vocab = (await db.execute(
        select(func.count(VocabBook.id)).where(VocabBook.mastered == True)
    )).scalar() or 0

    return {
        "total_users": total_users,
        "signups": {"today": today_signups, "week": week_signups, "month": month_signups},
        "active_users": {"dau": dau, "wau": wau, "mau": mau},
        "content": {
            "total_conversations": total_conversations,
            "total_vocab": total_vocab,
            "mastered_vocab": mastered_vocab,
        },
    }


# ══════════════════════════════════════════════════════════
# 2. 注册趋势 (每日)
# ══════════════════════════════════════════════════════════

@router.get("/signups/trend", dependencies=[Depends(verify_admin)])
async def signup_trend(days: int = 30, db: AsyncSession = Depends(get_db)):
    """每日新注册用户数"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    return [{"date": str(row.date), "count": row.count} for row in result]


# ══════════════════════════════════════════════════════════
# 3. DAU 趋势
# ══════════════════════════════════════════════════════════

@router.get("/dau/trend", dependencies=[Depends(verify_admin)])
async def dau_trend(days: int = 30, db: AsyncSession = Depends(get_db)):
    """每日活跃用户数"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(StudyStreak.date).label("date"),
            func.count(distinct(StudyStreak.user_id)).label("count"),
        )
        .where(StudyStreak.date >= since)
        .group_by(func.date(StudyStreak.date))
        .order_by(func.date(StudyStreak.date))
    )
    return [{"date": str(row.date), "count": row.count} for row in result]


# ══════════════════════════════════════════════════════════
# 4. 用户列表
# ══════════════════════════════════════════════════════════

@router.get("/users", dependencies=[Depends(verify_admin)])
async def user_list(
    page: int = 1,
    size: int = 50,
    search: Optional[str] = None,
    level: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """所有注册用户 — 分页 + 搜索/筛选"""
    offset = (page - 1) * size

    # 构建过滤条件
    filters = []
    if search:
        like_pat = f"%{search}%"
        filters.append(or_(User.email.ilike(like_pat), User.nickname.ilike(like_pat)))
    if level:
        try:
            filters.append(User.korean_level == KoreanLevel(level))
        except ValueError:
            pass
    if active is not None:
        filters.append(User.is_active == active)

    base_q = select(User)
    count_q = select(func.count(User.id))
    if filters:
        base_q = base_q.where(and_(*filters))
        count_q = count_q.where(and_(*filters))

    total = (await db.execute(count_q)).scalar() or 0

    result = await db.execute(
        base_q.order_by(User.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "nickname": u.nickname,
                "level": u.korean_level.value if u.korean_level else "beginner",
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "is_active": u.is_active,
            }
            for u in users
        ],
    }


# ══════════════════════════════════════════════════════════
# 5. 单个用户详情
# ══════════════════════════════════════════════════════════

@router.get("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def user_detail(user_id: int, db: AsyncSession = Depends(get_db)):
    """用户详情 + 学习统计"""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    # 对话数
    conv_count = (await db.execute(
        select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    )).scalar() or 0

    # 词汇数
    vocab_count = (await db.execute(
        select(func.count(VocabBook.id)).where(VocabBook.user_id == user_id)
    )).scalar() or 0

    # 总学习分钟数
    total_minutes = (await db.execute(
        select(func.coalesce(func.sum(StudyStreak.minutes_studied), 0))
        .where(StudyStreak.user_id == user_id)
    )).scalar() or 0

    # 连续打卡天数
    streak_days = (await db.execute(
        select(func.count(StudyStreak.id)).where(StudyStreak.user_id == user_id)
    )).scalar() or 0

    # 最近活跃
    last_active = (await db.execute(
        select(func.max(StudyStreak.date)).where(StudyStreak.user_id == user_id)
    )).scalar()

    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "level": user.korean_level.value if user.korean_level else "beginner",
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "is_active": user.is_active,
        "stats": {
            "conversations": conv_count,
            "vocab_words": vocab_count,
            "total_minutes": total_minutes,
            "study_days": streak_days,
            "last_active": last_active.isoformat() if last_active else None,
        },
    }


# ══════════════════════════════════════════════════════════
# 6. 等级分布
# ══════════════════════════════════════════════════════════

@router.get("/levels", dependencies=[Depends(verify_admin)])
async def level_distribution(db: AsyncSession = Depends(get_db)):
    """用户韩语等级分布"""
    result = await db.execute(
        select(User.korean_level, func.count(User.id))
        .group_by(User.korean_level)
    )
    return {str(row[0].value) if row[0] else "unknown": row[1] for row in result}


# ══════════════════════════════════════════════════════════
# 7. 学习时长统计
# ══════════════════════════════════════════════════════════

@router.get("/study/trend", dependencies=[Depends(verify_admin)])
async def study_trend(days: int = 30, db: AsyncSession = Depends(get_db)):
    """每日总学习分钟数"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(StudyStreak.date).label("date"),
            func.coalesce(func.sum(StudyStreak.minutes_studied), 0).label("minutes"),
        )
        .where(StudyStreak.date >= since)
        .group_by(func.date(StudyStreak.date))
        .order_by(func.date(StudyStreak.date))
    )
    return [{"date": str(row.date), "minutes": row.minutes} for row in result]


# ══════════════════════════════════════════════════════════
# 8. 用户管理 — 禁用/启用
# ══════════════════════════════════════════════════════════

@router.patch("/users/{user_id}/toggle", dependencies=[Depends(verify_admin)])
async def toggle_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """切换用户 is_active 状态"""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "is_active": user.is_active}


# ══════════════════════════════════════════════════════════
# 9. 用户管理 — 编辑信息
# ══════════════════════════════════════════════════════════

@router.patch("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def update_user(
    user_id: int,
    nickname: Optional[str] = Body(None),
    korean_level: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
):
    """编辑用户昵称 / 韩语等级"""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    if nickname is not None:
        user.nickname = nickname
    if korean_level is not None:
        try:
            user.korean_level = KoreanLevel(korean_level)
        except ValueError:
            raise HTTPException(400, f"Invalid level: {korean_level}")
    await db.commit()
    await db.refresh(user)
    return {
        "id": user.id,
        "nickname": user.nickname,
        "level": user.korean_level.value if user.korean_level else "beginner",
    }


# ══════════════════════════════════════════════════════════
# 10. 用户管理 — 软删除
# ══════════════════════════════════════════════════════════

@router.delete("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """软删除用户 (设 is_active=False)"""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = False
    await db.commit()
    return {"id": user.id, "deleted": True}


# ══════════════════════════════════════════════════════════
# 11. 数据导出 — 用户列表
# ══════════════════════════════════════════════════════════

@router.get("/export/users", dependencies=[Depends(verify_admin)])
async def export_users(db: AsyncSession = Depends(get_db)):
    """全量用户列表 (前端转 CSV)"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "nickname": u.nickname,
            "level": u.korean_level.value if u.korean_level else "beginner",
            "daily_goal_minutes": u.daily_goal_minutes,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "is_active": u.is_active,
        }
        for u in users
    ]


# ══════════════════════════════════════════════════════════
# 12. 数据导出 — 统计概览
# ══════════════════════════════════════════════════════════

@router.get("/export/overview", dependencies=[Depends(verify_admin)])
async def export_overview(db: AsyncSession = Depends(get_db)):
    """KPI 汇总 (前端转 CSV)"""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    today_signups = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= today)
    )).scalar() or 0
    week_signups = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )).scalar() or 0
    month_signups = (await db.execute(
        select(func.count(User.id)).where(User.created_at >= month_ago)
    )).scalar() or 0
    dau = (await db.execute(
        select(func.count(distinct(StudyStreak.user_id))).where(StudyStreak.date >= today)
    )).scalar() or 0
    wau = (await db.execute(
        select(func.count(distinct(StudyStreak.user_id))).where(StudyStreak.date >= week_ago)
    )).scalar() or 0
    mau = (await db.execute(
        select(func.count(distinct(StudyStreak.user_id))).where(StudyStreak.date >= month_ago)
    )).scalar() or 0
    total_conv = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    total_vocab = (await db.execute(select(func.count(VocabBook.id)))).scalar() or 0

    return [
        {"metric": "Total Users / 전체 사용자", "value": total_users},
        {"metric": "Today Signups / 오늘 가입", "value": today_signups},
        {"metric": "7-Day Signups / 7일 가입", "value": week_signups},
        {"metric": "30-Day Signups / 30일 가입", "value": month_signups},
        {"metric": "DAU / 일간 활성", "value": dau},
        {"metric": "WAU / 주간 활성", "value": wau},
        {"metric": "MAU / 월간 활성", "value": mau},
        {"metric": "Total Conversations / 전체 대화", "value": total_conv},
        {"metric": "Total Vocab / 전체 단어", "value": total_vocab},
        {"metric": "Export Date / 내보내기 날짜", "value": now.isoformat()},
    ]
