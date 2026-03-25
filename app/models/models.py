"""
数据库模型 —— 用户 / 课程 / 学习进度 / 对话记录 / 词汇本
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import get_settings
from app.core.database import Base

# PostgreSQL → JSONB (索引/查询优化), SQLite → JSON
_JsonCol = JSONB if "postgres" in get_settings().DATABASE_URL else JSON


# ── 枚举 ──
class KoreanLevel(str, enum.Enum):
    BEGINNER = "beginner"       # TOPIK 1-2
    INTERMEDIATE = "intermediate"  # TOPIK 3-4
    ADVANCED = "advanced"        # TOPIK 5-6


class LessonCategory(str, enum.Enum):
    MEETING = "meeting"
    EMAIL = "email"
    PHONE = "phone"
    NEGOTIATION = "negotiation"
    SOCIAL = "social"
    DRAMA = "drama"
    GRAMMAR = "grammar"


# ── 用户 ──
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(String(100), default="")
    korean_level: Mapped[KoreanLevel] = mapped_column(
        Enum(KoreanLevel), default=KoreanLevel.BEGINNER
    )
    daily_goal_minutes: Mapped[int] = mapped_column(Integer, default=15)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # relationships
    progress: Mapped[list["LearningProgress"]] = relationship(back_populates="user")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
    vocab_book: Mapped[list["VocabBook"]] = relationship(back_populates="user")


# ── 课程内容 ──
class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    title_ko: Mapped[str] = mapped_column(String(200), default="")
    category: Mapped[LessonCategory] = mapped_column(Enum(LessonCategory))
    level: Mapped[KoreanLevel] = mapped_column(Enum(KoreanLevel))
    description: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[dict] = mapped_column(_JsonCol, default=dict)
    # content JSONB 存储灵活内容：词汇列表、语法点、对话脚本、韩剧台词等
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("ix_lessons_category_level", "category", "level"),)


# ── 学习进度 ──
class LearningProgress(Base):
    __tablename__ = "learning_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"), index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    quiz_results: Mapped[dict | None] = mapped_column(_JsonCol, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="progress")

    __table_args__ = (
        Index("ix_progress_user_lesson", "user_id", "lesson_id", unique=True),
    )


# ── 对话记录 ──
class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    messages: Mapped[list] = mapped_column(_JsonCol, default=list)
    # messages: [{"role": "user/assistant", "content": "...", "timestamp": "..."}]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="conversations")


# ── 生词本 ──
class VocabBook(Base):
    __tablename__ = "vocab_book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    word_ko: Mapped[str] = mapped_column(String(100))
    word_romanized: Mapped[str] = mapped_column(String(200), default="")
    meaning_zh: Mapped[str] = mapped_column(String(300))
    example_sentence: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(_JsonCol, default=list)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="vocab_book")

    __table_args__ = (
        Index("ix_vocab_user_word", "user_id", "word_ko"),
    )


# ── 学习打卡 ──
class StudyStreak(Base):
    __tablename__ = "study_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    minutes_studied: Mapped[int] = mapped_column(Integer, default=0)
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    quiz_score_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    pronunciation_score_avg: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_streak_user_date", "user_id", "date", unique=True),
    )
