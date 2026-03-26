"""
API 数据模型 (Pydantic schemas)
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


# ── Auth ──
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nickname: str = ""
    korean_level: str = "beginner"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class MicrosoftAuthRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int


class UserProfile(BaseModel):
    id: int
    email: str
    nickname: str
    korean_level: str
    daily_goal_minutes: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Chat ──
class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    tool_calls: list[str] = []
    reply_audio_base64: str | None = None


class TtsRequest(BaseModel):
    text: str


# ── Voice ──
class VoiceChatRequest(BaseModel):
    audio_base64: str
    thread_id: str | None = None
    language: str = "ko-KR"


class VoiceChatResponse(BaseModel):
    reply_text: str
    reply_audio_base64: str
    user_transcript: str
    thread_id: str


class PronunciationRequest(BaseModel):
    audio_base64: str
    reference_text: str
    language: str = "ko-KR"


class PronunciationResult(BaseModel):
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    pronunciation_score: float
    words: list[dict]


# ── Progress ──
class ProgressResponse(BaseModel):
    total_lessons: int
    completed_lessons: int
    current_streak_days: int
    total_study_minutes: int
    avg_pronunciation_score: float | None


class StudyStreakResponse(BaseModel):
    date: str
    minutes_studied: int
    lessons_completed: int


# ── Vocab ──
class VocabAddRequest(BaseModel):
    word_ko: str
    word_romanized: str = ""
    meaning_zh: str
    example_sentence: str = ""
    tags: list[str] = []


class VocabResponse(BaseModel):
    id: int
    word_ko: str
    word_romanized: str
    meaning_zh: str
    example_sentence: str
    tags: list[str]
    mastered: bool
    review_count: int

    model_config = {"from_attributes": True}


# ── Lessons ──
class LessonSummary(BaseModel):
    id: int
    title: str
    title_ko: str
    category: str
    level: str
    description: str

    model_config = {"from_attributes": True}
