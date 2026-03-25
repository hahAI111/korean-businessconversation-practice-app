# 🗄️ Data Architecture / 데이터 아키텍처

> Dual database strategy + Redis cache — how data is stored, accessed, and flows through the system.
>
> 듀얼 데이터베이스 전략 + Redis 캐시 — 데이터가 어떻게 저장되고, 접근되고, 시스템을 통해 흐르는지.

---

## Table of Contents / 목차

1. [Dual Database Strategy / 듀얼 DB 전략](#1-dual-database-strategy--듀얼-db-전략)
2. [PostgreSQL — Relational Data / 관계형 데이터](#2-postgresql--relational-data--관계형-데이터)
3. [Cosmos DB — Document Data / 문서형 데이터](#3-cosmos-db--document-data--문서형-데이터)
4. [Redis — Cache Layer / 캐시 계층](#4-redis--cache-layer--캐시-계층)
5. [Data Flow Diagrams / 데이터 흐름 다이어그램](#5-data-flow-diagrams--데이터-흐름-다이어그램)
6. [Fallback Strategy / 대체 전략](#6-fallback-strategy--대체-전략)

---

## 1. Dual Database Strategy / 듀얼 DB 전략

The system uses **two databases** — each optimized for its data type:

시스템은 **두 개의 데이터베이스**를 사용하며, 각각 데이터 유형에 최적화되어 있습니다:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│                    애플리케이션 계층                           │
└──────────┬──────────────────┬──────────────────┬────────────┘
           │                  │                  │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌───────▼───────┐
    │ PostgreSQL  │   │ Cosmos DB   │   │    Redis      │
    │             │   │             │   │               │
    │ Structured  │   │ Flexible    │   │ Ephemeral     │
    │ 구조화      │   │ 유연한      │   │ 일시적        │
    │             │   │             │   │               │
    │ Users       │   │ Conver-     │   │ Sessions      │
    │ Vocab       │   │ sations     │   │ Rate limits   │
    │ Streaks     │   │ K-Drama     │   │ Study time    │
    │ Lessons     │   │ Events      │   │ Streaks       │
    └─────────────┘   └─────────────┘   └───────────────┘
    
    Relational         Document           Cache
    관계형              문서형              캐시
    Consistent         Flexible            Fast
    일관성              유연성              빠름
```

### Why two databases? / 왜 두 개의 데이터베이스인가?

| Need / 필요 | PostgreSQL ✅ | Cosmos DB ✅ |
|---|---|---|
| User accounts with strict schema / 엄격한 스키마의 사용자 계정 | ✅ Best fit / 최적 | ❌ Overkill |
| Flexible conversation history / 유연한 대화 기록 | ❌ JSONB works but messy / 가능하지만 복잡 | ✅ Natural fit / 자연스러운 적합 |
| Vocabulary with relations / 관계가 있는 단어장 | ✅ Foreign keys / 외래 키 | ❌ No relations |
| K-drama content with nested dialogue / 중첩 대화가 있는 드라마 콘텐츠 | ❌ Poor fit | ✅ Document model / 문서 모델 |
| Learning events (append-only) / 학습 이벤트 (추가 전용) | ❌ Table bloat / 테이블 비대화 | ✅ Partitioned by user / 사용자별 파티션 |

---

## 2. PostgreSQL — Relational Data / 관계형 데이터

**Engine**: PostgreSQL 14 Flexible Server (production) / SQLite (local dev)
**ORM**: SQLAlchemy 2.0 async (`asyncpg` driver)
**Connection**: Private endpoint via VNet (no public access)

### 2.1 Tables / 테이블

#### `users` — User Accounts / 사용자 계정

| Column / 컬럼 | Type / 타입 | Description / 설명 |
|---|---|---|
| `id` | Integer PK | Auto-increment primary key / 자동 증가 기본 키 |
| `email` | String(255) UNIQUE | Login email / 로그인 이메일 |
| `hashed_password` | String(255) | bcrypt hash / bcrypt 해시 |
| `nickname` | String(100) | Display name / 표시 이름 |
| `korean_level` | Enum | `beginner` / `intermediate` / `advanced` |
| `daily_goal_minutes` | Integer | Daily study target (default: 30) / 일일 학습 목표 (기본값: 30분) |
| `created_at` | DateTime | Registration timestamp / 가입 시각 |
| `is_active` | Boolean | Account active status / 계정 활성 상태 |

#### `lessons` — Course Content / 강의 내용

| Column / 컬럼 | Type / 타입 | Description / 설명 |
|---|---|---|
| `id` | Integer PK | Primary key / 기본 키 |
| `title` | String(200) | English title / 영어 제목 |
| `title_ko` | String(200) | Korean title / 한국어 제목 |
| `category` | Enum | `meeting` / `email` / `phone` / `negotiation` / `social` / `drama` / `grammar` |
| `level` | Enum | `beginner` / `intermediate` / `advanced` |
| `description` | Text | Lesson description / 강의 설명 |
| `content` | JSON/JSONB | Flexible lesson content (dialogue, exercises, etc.) / 유연한 강의 콘텐츠 |
| `sort_order` | Integer | Display order / 표시 순서 |
| `is_published` | Boolean | Published status / 게시 상태 |
| `created_at` | DateTime | Creation timestamp / 생성 시각 |

#### `learning_progress` — Progress Tracking / 진도 추적

| Column / 컬럼 | Type / 타입 | Description / 설명 |
|---|---|---|
| `id` | Integer PK | Primary key / 기본 키 |
| `user_id` | Integer FK → users | User reference / 사용자 참조 |
| `lesson_id` | Integer FK → lessons | Lesson reference / 강의 참조 |
| `completed` | Boolean | Completion status / 완료 상태 |
| `score` | Float | Lesson score / 강의 점수 |
| `quiz_results` | JSON/JSONB | Detailed quiz answers and scores / 상세 퀴즈 답변 및 점수 |
| `time_spent_seconds` | Integer | Time spent on lesson / 강의 소요 시간 |
| `completed_at` | DateTime | Completion timestamp / 완료 시각 |
| `updated_at` | DateTime | Last update / 최종 업데이트 |

#### `vocab_book` — Vocabulary Book / 단어장

| Column / 컬럼 | Type / 타입 | Description / 설명 |
|---|---|---|
| `id` | Integer PK | Primary key / 기본 키 |
| `user_id` | Integer FK → users | Owner / 소유자 |
| `word_ko` | String(100) | Korean word / 한국어 단어 |
| `word_romanized` | String(200) | Romanization / 로마자 표기 |
| `meaning_zh` | String(500) | Chinese meaning / 중국어 뜻 |
| `example_sentence` | Text | Example usage / 예문 |
| `tags` | JSON/JSONB | Categorization tags / 분류 태그 |
| `mastered` | Boolean | Mastered flag (default: false) / 마스터 플래그 |
| `review_count` | Integer | Times reviewed / 복습 횟수 |
| `next_review_at` | DateTime | Spaced repetition schedule / 간격 반복 일정 |
| `created_at` | DateTime | Added timestamp / 추가 시각 |

#### `study_streak` — Daily Study Records / 일일 학습 기록

| Column / 컬럼 | Type / 타입 | Description / 설명 |
|---|---|---|
| `id` | Integer PK | Primary key / 기본 키 |
| `user_id` | Integer FK → users | User reference / 사용자 참조 |
| `date` | Date UNIQUE(user_id, date) | Study date / 학습 날짜 |
| `minutes_studied` | Integer | Total minutes / 총 학습 분 |
| `lessons_completed` | Integer | Lessons finished / 완료한 강의 수 |
| `quiz_score_avg` | Float | Average quiz score / 평균 퀴즈 점수 |
| `pronunciation_score_avg` | Float | Average pronunciation score / 평균 발음 점수 |

### 2.2 Enums / 열거형

```python
class KoreanLevel(str, Enum):
    beginner = "beginner"         # 초급
    intermediate = "intermediate" # 중급
    advanced = "advanced"         # 고급

class LessonCategory(str, Enum):
    meeting = "meeting"           # 회의
    email = "email"               # 이메일
    phone = "phone"               # 전화
    negotiation = "negotiation"   # 협상
    social = "social"             # 사교
    drama = "drama"               # 드라마
    grammar = "grammar"           # 문법
```

### 2.3 Entity Relationship / 엔티티 관계

```
┌──────────┐     1:N     ┌─────────────────┐
│  users   │◄────────────│  vocab_book     │
│  사용자   │             │  단어장          │
└────┬─────┘             └─────────────────┘
     │
     │ 1:N     ┌─────────────────┐
     ├────────►│ learning_progress│
     │         │ 학습 진도         │
     │         └────────┬────────┘
     │                  │ N:1
     │         ┌────────▼────────┐
     │         │    lessons      │
     │         │    강의          │
     │         └─────────────────┘
     │
     │ 1:N     ┌─────────────────┐
     └────────►│  study_streak   │
               │  연속 학습       │
               └─────────────────┘
```

---

## 3. Cosmos DB — Document Data / 문서형 데이터

**API**: NoSQL (document model)
**Auth**: Entra ID (DefaultAzureCredential, no API key)
**Fallback**: Empty COSMOS_ENDPOINT → automatic in-memory mock

### 3.1 Containers / 컨테이너

#### `conversations` — Chat History / 대화 기록

```json
// Partition key: /user_id / 파티션 키: /user_id
{
    "id": "conv_abc123",
    "user_id": "42",
    "thread_id": "thread_abc123def456",
    "title": "Meeting vocabulary practice / 회의 어휘 연습",
    "messages": [
        {
            "role": "user",
            "content": "How do I say 'Let's start the meeting'? / '회의를 시작합시다'는 어떻게 말해요?",
            "timestamp": "2026-03-25T10:00:00Z"
        },
        {
            "role": "assistant",
            "content": "Great question! In natural Korean... / 좋은 질문이에요! 자연스러운 한국어로는...",
            "timestamp": "2026-03-25T10:00:05Z"
        }
    ],
    "message_count": 12,
    "created_at": "2026-03-25T10:00:00Z",
    "updated_at": "2026-03-25T10:30:00Z"
}
```

#### `drama_content` — K-Drama Teaching Material / 드라마 교재

```json
// Partition key: /drama_id / 파티션 키: /drama_id
{
    "id": "drama_misaeng_001",
    "drama_id": "misaeng",
    "title": "미생 (Incomplete Life)",
    "episode": "S01E03",
    "scene_description": "New employee first meeting / 신입사원 첫 회의",
    "dialogue": [
        {
            "speaker": "장그래",
            "korean": "안녕하세요, 처음 뵙겠습니다.",
            "romanization": "annyeonghaseyo, cheoeum boepgesseumnida",
            "translation": "Hello, nice to meet you for the first time."
        }
    ],
    "vocabulary_notes": [...],
    "grammar_points": [...]
}
```

#### `learning_events` — Activity Log / 활동 로그

```json
// Partition key: /user_id / 파티션 키: /user_id
{
    "id": "evt_xyz789",
    "user_id": "42",
    "event_type": "voice_chat",     // or: text_chat, pronunciation, vocab_add, checkin
    "payload": {
        "duration_seconds": 120,
        "language_detected": "zh-CN",
        "thread_id": "thread_abc123"
    },
    "timestamp": "2026-03-25T10:15:00Z"
}
```

### 3.2 Cosmos DB Operations / Cosmos DB 작업

| Operation / 작업 | Method / 메서드 | Description / 설명 |
|---|---|---|
| `create_conversation()` | `container.create_item()` | Save new conversation / 새 대화 저장 |
| `append_message()` | `container.patch_item()` | Add message to existing conversation / 기존 대화에 메시지 추가 |
| `get_conversation()` | `container.read_item()` | Load conversation by thread_id / thread_id로 대화 로드 |
| `list_conversations()` | `container.query_items()` | List user's conversations / 사용자 대화 목록 |
| `upsert_drama()` | `container.upsert_item()` | Create or update drama content / 드라마 콘텐츠 생성/업데이트 |
| `log_event()` | `container.create_item()` | Append learning event / 학습 이벤트 추가 |

---

## 4. Redis — Cache Layer / 캐시 계층

**Purpose**: Fast ephemeral data — sessions, rate limits, and real-time counters.

**용도**: 빠른 일시적 데이터 — 세션, 속도 제한, 실시간 카운터.

### 4.1 Key Design / 키 설계

| Key Pattern / 키 패턴 | Type / 타입 | TTL | Description / 설명 |
|---|---|---|---|
| `thread:{user_id}` | String | 24h | Current conversation thread ID for user / 현재 대화 스레드 ID |
| `ctx:{thread_id}` | JSON String | 1h | Cached conversation context / 캐시된 대화 컨텍스트 |
| `study:{user_id}:today` | Integer | 25h | Today's accumulated study seconds / 오늘 누적 학습 시간(초) |
| `streak:{user_id}` | Integer | 48h | Consecutive study days count / 연속 학습일 수 |
| `rl:{user_id}` | Integer | 60s | Rate limit counter (max 60/min) / 속도 제한 카운터 (최대 60회/분) |

### 4.2 Cache Operations / 캐시 작업

```python
# Thread management / 스레드 관리
await cache.get_thread_id(user_id) → str | None
await cache.set_thread_id(user_id, thread_id, ttl=86400)

# Conversation context / 대화 컨텍스트
await cache.cache_conversation_context(thread_id, context, ttl=3600)
await cache.get_conversation_context(thread_id) → dict | None

# Study tracking / 학습 추적
await cache.record_study_session(user_id, minutes)
await cache.get_today_study_minutes(user_id) → int

# Streak tracking / 연속 학습 추적
await cache.get_streak(user_id) → int
await cache.set_streak(user_id, days, ttl=172800)

# Rate limiting / 속도 제한
await cache.check_rate_limit(user_id, limit=60, window=60) → bool

# Generic JSON cache / 범용 JSON 캐시
await cache.get_json(key) → dict | None
await cache.set_json(key, value, ttl=3600)
```

### 4.3 Connection Modes / 연결 모드

| Mode / 모드 | `_auth_mode` | When / 조건 | Behavior / 동작 |
|---|---|---|---|
| **Production** | `"access-key"` | `REDIS_URL=rediss://...` | Real Azure Redis with SSL / 실제 Azure Redis (SSL) |
| **Local Dev** | `"fake"` | `REDIS_URL=fake` | `fakeredis` in-memory / 인메모리 fakeredis |
| **Fallback** | `"memory-fallback"` | Connection failure / 연결 실패 | Python dict with TTL tracking / TTL 추적 dict |
| **Not Connected** | `"not-connected"` | Before init / 초기화 전 | Returns None for all reads / 모든 읽기에 None 반환 |

---

## 5. Data Flow Diagrams / 데이터 흐름 다이어그램

### 5.1 Text Chat Data Flow / 텍스트 대화 데이터 흐름

```
User sends message / 사용자 메시지 전송
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  POST /api/chat                                          │
│                                                          │
│  1. JWT → user_id                     [Auth / 인증]      │
│  2. Redis: rl:{user_id} → check      [Rate limit / 제한] │
│  3. Redis: thread:{user_id} → get     [Thread / 스레드]  │
│     └─ if none → create new thread                       │
│  4. GPT Agent → AI reply              [AI processing]    │
│  5. Return reply to user              [Response / 응답]   │
│                                                          │
│  Background (fire-and-forget) / 백그라운드:               │
│  6. Redis: study:{uid}:today → incr   [Study time / 시간]│
│  7. Cosmos: conversations → append    [Save chat / 저장] │
│  8. Cosmos: learning_events → create  [Log event / 기록] │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Voice Chat Data Flow / 음성 대화 데이터 흐름

```
WebSocket connection / WebSocket 연결
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  WS /ws/voice                                                │
│                                                              │
│  1. {"type":"start","token":"JWT"}                            │
│     └─ JWT verify → user_id                                  │
│     └─ Redis: thread:{user_id} → get/create                  │
│                                                              │
│  2. Binary audio frames → collect in buffer                  │
│     바이너리 오디오 프레임 → 버퍼에 수집                        │
│                                                              │
│  3. {"type":"end_audio"}                                     │
│     └─ Buffer → WAV 16kHz mono resampling                    │
│     └─ Azure Speech STT (auto-detect ko/en/zh)               │
│     └─ Recognized text → GPT Agent (VOICE_INSTRUCTIONS)      │
│     └─ AI reply → Azure Speech TTS (SunHiNeural SSML)        │
│     └─ {"type":"transcript"} + {"type":"reply"} + Binary MP3 │
│                                                              │
│  Background / 백그라운드:                                     │
│     └─ Redis: study time increment / 학습 시간 증가           │
│     └─ Cosmos: save conversation + log event / 대화 저장      │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 Vocabulary Data Flow / 단어장 데이터 흐름

```
┌──────────────┐     POST /api/vocab      ┌───────────────┐
│  User adds   │ ──────────────────────► │  PostgreSQL    │
│  new word    │                         │  vocab_book    │
│  새 단어 추가 │ ◄────────────────────── │  table         │
│              │     VocabResponse        │                │
└──────────────┘                         └───────────────┘

┌──────────────┐     PATCH /vocab/{id}   ┌───────────────┐
│  Mark as     │ ──────────────────────► │  vocab_book    │
│  mastered    │ ◄────────────────────── │  mastered=true │
│  마스터 표시  │     {mastered: true}    │                │
└──────────────┘                         └───────────────┘
```

### 5.4 Progress & Streak Data Flow / 진도 & 연속 학습 데이터 흐름

```
┌──────────────────────────────────────────────────────────┐
│  Progress Dashboard Request / 진도 대시보드 요청          │
│  GET /api/progress                                       │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │  PostgreSQL       │  │  Redis            │             │
│  │                   │  │                   │             │
│  │  users           ─┘  │  streak:{uid}    ─┘             │
│  │  lessons          │  │  study:{uid}:today│             │
│  │  learning_progress│  │                   │             │
│  │  study_streak     │  └───────────────────┘             │
│  └───────────────────┘                                   │
│                                                          │
│  Combined response / 결합된 응답:                         │
│  {total_lessons, completed, streak_days,                 │
│   study_minutes_today, avg_pronunciation}                │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Fallback Strategy / 대체 전략

The system is designed to **never crash** due to a database/cache failure. Every external dependency has a fallback.

시스템은 데이터베이스/캐시 장애로 인해 **절대 크래시되지 않도록** 설계되었습니다. 모든 외부 의존성에 대체 방안이 있습니다.

```
┌────────────────┐     Failure / 실패     ┌─────────────────────┐
│  PostgreSQL    │ ──────────────────────► │  Error response     │
│                │  (Critical — no        │  (User cannot login  │
│                │   fallback for user    │   or save vocab)     │
│                │   data)               │  사용자 데이터는      │
│                │                        │  대체 불가            │
└────────────────┘                        └─────────────────────┘

┌────────────────┐     Failure / 실패     ┌─────────────────────┐
│  Cosmos DB     │ ──────────────────────► │  In-memory mock     │
│                │                        │  메모리 mock         │
│                │  Auto-detected         │  (conversations      │
│                │  자동 감지              │   not persisted)     │
│                │                        │  (대화 저장 안 됨)    │
└────────────────┘                        └─────────────────────┘

┌────────────────┐     Failure / 실패     ┌─────────────────────┐
│  Redis         │ ──────────────────────► │  In-memory dict     │
│                │                        │  메모리 dict          │
│                │  Auto-detected         │  (rate limits reset  │
│                │  자동 감지              │   on restart)        │
│                │                        │  (재시작 시 초기화)   │
└────────────────┘                        └─────────────────────┘
```

---

## Navigation / 탐색

| Next / 다음 | Document / 문서 |
|---|---|
| How the AI works / AI 작동 방식 | → [docs/AI_ENGINE.md](AI_ENGINE.md) |
| All files explained / 모든 파일 설명 | → [docs/CODEBASE.md](CODEBASE.md) |
| Network & deployment / 네트워크 & 배포 | → [docs/NETWORK.md](NETWORK.md) |
| BMAD methodology / BMAD 방법론 | → [docs/BMAD.md](BMAD.md) |
