"""
学习进度 + 课程 API
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.core.database import get_db
from app.models.models import Lesson, LearningProgress, StudyStreak
from app.schemas.schemas import LessonSummary, ProgressResponse, StudyStreakResponse
from app.services.cache_service import cache_service

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    total = (await db.execute(select(func.count(Lesson.id)))).scalar() or 0
    completed = (
        await db.execute(
            select(func.count(LearningProgress.id)).where(
                LearningProgress.user_id == user_id,
                LearningProgress.completed.is_(True),
            )
        )
    ).scalar() or 0

    streak_days = await cache_service.get_streak(user_id)
    today_minutes = await cache_service.get_today_study_minutes(user_id)

    return ProgressResponse(
        total_lessons=total,
        completed_lessons=completed,
        current_streak_days=streak_days,
        total_study_minutes=today_minutes,
        avg_pronunciation_score=None,
    )


@router.get("/lessons", response_model=list[LessonSummary])
async def list_lessons(
    category: str | None = None,
    level: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Lesson).where(Lesson.is_published.is_(True))
    if category:
        query = query.where(Lesson.category == category)
    if level:
        query = query.where(Lesson.level == level)
    query = query.order_by(Lesson.sort_order)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/streaks", response_model=list[StudyStreakResponse])
async def get_streaks(
    days: int = 30,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudyStreak)
        .where(StudyStreak.user_id == user_id)
        .order_by(StudyStreak.date.desc())
        .limit(days)
    )
    streaks = result.scalars().all()
    return [
        StudyStreakResponse(
            date=s.date.strftime("%Y-%m-%d"),
            minutes_studied=s.minutes_studied,
            lessons_completed=s.lessons_completed,
        )
        for s in streaks
    ]


@router.post("/checkin")
async def checkin(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """学习打卡 — 每日签到，记录学习活动并更新连续天数"""
    today = datetime.now(timezone.utc).date()
    today_dt = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)

    # Check if already checked in today
    result = await db.execute(
        select(StudyStreak).where(
            StudyStreak.user_id == user_id,
            func.date(StudyStreak.date) == today,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "checked_in": True,
            "already": True,
            "minutes_today": existing.minutes_studied,
            "message": "今天已经打卡了！继续加油 💪",
        }

    # Create today's streak record
    streak = StudyStreak(
        user_id=user_id,
        date=today_dt,
        minutes_studied=0,
        lessons_completed=0,
    )
    db.add(streak)
    await db.commit()

    # Update streak count in cache
    # Count consecutive days
    result = await db.execute(
        select(StudyStreak)
        .where(StudyStreak.user_id == user_id)
        .order_by(StudyStreak.date.desc())
        .limit(60)
    )
    all_streaks = result.scalars().all()
    consecutive = 0
    for i, s in enumerate(all_streaks):
        expected = today - timedelta(days=i)
        if s.date.date() == expected:
            consecutive += 1
        else:
            break
    await cache_service.set_streak(user_id, consecutive)

    return {
        "checked_in": True,
        "already": False,
        "streak_days": consecutive,
        "message": f"打卡成功！连续学习 {consecutive} 天 🔥",
    }
