---
stepsCompleted: [context, components, auth, data, voice, cache, deployment, review]
inputDocuments: [PRD.md, codebase-scan]
workflowType: 'architecture'
bmadAgent: 'Architect Winston'
bmadVersion: '6.2.2'
lastUpdated: '2026-03-27'
---

# Architecture Document
## Korean Biz Coach — System Architecture

> **BMAD Agent**: Architect Winston (System Architect) | **Phase**: 2-Solutioning
> **Status**: Living Document — reflects current production state

### 1. System Context

```
Users (Web Browser / PWA)
        │
        ▼
Azure App Service (FastAPI, B1 Linux, VNet Integrated)
   ├── REST API (auth, chat, vocab, progress, pronunciation, admin)
   ├── WebSocket (real-time voice conversation)
   ├── MCP Server (9 teaching tools for AI agent)
   └── Static Files (6 HTML pages, PWA-enabled)
        │
        ├──► Azure AI Foundry (GPT-5-nano + MCP tools + Responses API)
        ├──► Azure Speech Service (STT / TTS / Pronunciation Assessment)
        ├──► Azure PostgreSQL (relational: users, lessons, progress, vocab, streaks)
        ├──► Azure Cosmos DB (documents: conversations, drama, learning events)
        ├──► Azure Redis Cache (sessions, verification codes, rate-limit, context)
        └──► Azure Communication Services (email verification codes)
```

### 2. Authentication Architecture

#### 2.1 User Authentication — Dual Auth System

```
┌─────────────────────────────────────────────────────────────┐
│                     User Auth Flows                          │
├─────────────────────┬────────────────────┬──────────────────┤
│  Flow A: Email+Code │  Flow B: Password  │ Flow C: Entra ID │
│                     │                    │                   │
│  1. POST send-code  │  1. POST login     │ 1. MSAL.js popup  │
│  2. ACS sends email │  2. bcrypt verify  │ 2. id_token       │
│  3. POST register   │  3. HS256 JWT      │ 3. POST microsoft │
│     (with code)     │                    │ 4. JWKS validate  │
│  4. bcrypt hash     │                    │ 5. Auto-create    │
│  5. HS256 JWT       │                    │ 6. HS256 JWT      │
└─────────────────────┴────────────────────┴──────────────────┘
                              │
                              ▼
                   All subsequent requests:
                   Authorization: Bearer <JWT>
                   JWT claims: {sub: user_id, exp, iat}
```

#### 2.2 Azure Service Authentication — No API Keys

| Service | Auth Method | Mechanism |
|---------|------------|-----------|
| AI Foundry | `DefaultAzureCredential` | Managed Identity → Bearer token |
| Speech | `DefaultAzureCredential` | Managed Identity → Bearer token (REST) |
| Cosmos DB | `DefaultAzureCredential` | Entra ID (no keys) |
| PostgreSQL | Password auth | Connection string (VNet private) |
| Redis | Access key | URL with password (VNet private, SSL) |
| ACS Email | HMAC-SHA256 | Connection string signature |

### 3. Component Architecture

```
app/
├── main.py                     # FastAPI app, lifespan, CORS, routes
├── core/
│   ├── config.py               # Pydantic Settings (30+ config vars)
│   ├── database.py             # Async SQLAlchemy engine (PostgreSQL/SQLite)
│   ├── cosmos.py               # Azure Cosmos DB async client + mock fallback
│   ├── redis.py                # Redis client (Azure/FakeRedis/memory) + diagnostics
│   └── auth.py                 # JWT create/verify + Microsoft JWKS validation
├── api/
│   ├── auth.py                 # send-code, register, login, microsoft, profile
│   ├── chat.py                 # Text chat + stream + TTS + diagnostics (7 endpoints)
│   ├── voice_ws.py             # WebSocket real-time voice pipeline
│   ├── admin.py                # Admin dashboard analytics (4 endpoints)
│   ├── pronunciation.py        # Pronunciation assessment scoring
│   ├── progress.py             # Lessons, progress, streaks, check-in
│   └── vocab.py                # Vocabulary CRUD + mastery toggle
├── models/
│   └── models.py               # 6 SQLAlchemy models + 2 enums
├── schemas/
│   └── schemas.py              # 15+ Pydantic request/response schemas
├── services/
│   ├── agent_service.py        # Azure AI Foundry Agent (text + voice + stream)
│   ├── speech_service.py       # Azure Speech STT/TTS/Pronunciation REST API
│   ├── cosmos_service.py       # Cosmos DB CRUD (conversations, drama, events)
│   ├── cache_service.py        # Redis caching with memory fallback
│   └── email_service.py        # ACS email verification codes
├── utils/                      # Utility modules
mcp_server/
│   └── server.py               # 9 FastMCP teaching tools
data/
│   └── business_korean.json    # Content data (vocab, grammar, dramas, scenarios)
static/
│   ├── index.html              # Login/Register (MSAL.js + email auth)
│   ├── chat.html               # AI chat + voice UI
│   ├── vocab.html              # Vocabulary book management
│   ├── progress.html           # Learning progress dashboard
│   ├── admin_dashboard.html    # Admin analytics panel
│   ├── offline.html            # PWA offline fallback
│   ├── app.js                  # Shared JS (Auth, Api, Toast)
│   ├── style.css               # Gold/navy theme, responsive
│   ├── service-worker.js       # PWA caching strategy
│   └── manifest.json           # PWA manifest + icons
```

### 4. Real-time Voice Architecture

```
Browser                    Server                    Azure
  │                          │                         │
  │ 1. WS connect            │                         │
  │    {"type":"start",      │                         │
  │     "token":"JWT"}       │                         │
  ├─────────────────────────►│ JWT validate             │
  │                          │ (_verify_token)          │
  │ 2. Audio chunk (binary)  │                         │
  ├─────────────────────────►│ accumulate               │
  │                          │                         │
  │ 3. {"type":"end_audio"}  │                         │
  ├─────────────────────────►│                         │
  │                          │ 4. Parallel STT          │
  │                          │    (ko-KR/en-US/zh-CN)   │
  │                          ├────────────────────────►│
  │                          │ 5. Transcript            │
  │                          │◄────────────────────────┤
  │ 6. {"transcript":"..."}  │                         │
  │◄─────────────────────────┤                         │
  │                          │ 7. AI Foundry voice_chat │
  │                          ├────────────────────────►│
  │                          │ 8. Reply text            │
  │                          │◄────────────────────────┤
  │ 9. {"reply":"..."}       │                         │
  │◄─────────────────────────┤                         │
  │                          │ 10. TTS SSML (SunHi)    │
  │                          ├────────────────────────►│
  │                          │ 11. MP3 audio            │
  │                          │◄────────────────────────┤
  │ 12. Binary audio (MP3)   │                         │
  │◄─────────────────────────┤                         │
  │                          │ 13. Background saves:    │
  │                          │   - Cosmos conversation  │
  │                          │   - Study session update │
  │                          │   - Learning event log   │
```

**Text input alternative**: User can also send `{"type":"text", "message":"..."}` to skip STT and go directly to AI agent.

### 5. Dual Database Architecture (双数据库架构)

#### 5.1 PostgreSQL — Relational Data (관계형 데이터)

| Table | Fields | Purpose |
|-------|--------|--------|
| **users** | id, email, hashed_password, nickname, korean_level, daily_goal_minutes, is_active, created_at | User accounts |
| **lessons** | id, title, title_ko, category, level, description, content(JSONB), sort_order, is_published | Teaching content |
| **learning_progress** | id, user_id(FK), lesson_id(FK), completed, score, quiz_results(JSONB), time_spent_seconds | Progress tracking |
| **vocab_book** | id, user_id(FK), word_ko, word_romanized, meaning_zh, example_sentence, tags(JSONB), mastered, review_count, next_review_at | Personal vocabulary |
| **study_streaks** | id, user_id(FK), date, minutes_studied, lessons_completed, quiz_score_avg, pronunciation_score_avg | Daily activity |
| **conversations** | id, user_id(FK), thread_id, title, messages(JSONB), created_at, updated_at | Chat history (legacy) |

**Enums**: `KoreanLevel` (beginner/intermediate/advanced), `LessonCategory` (meeting/email/phone/negotiation/social/drama/grammar)

#### 5.2 Cosmos DB — Document Data (문서형 데이터)

| Container | Partition Key | TTL | Purpose |
|-----------|--------------|-----|---------|
| **conversations** | `/user_id` | — | Chat conversations with nested messages array |
| **drama_content** | `/drama_id` | — | K-drama dialogues, cultural notes, flexible schema |
| **learning_events** | `/user_id` | 90 days | Analytics event stream (append-only) |

**Design Decisions:**
- **API**: NoSQL (SQL API) — SQL-like queries, best SDK support
- **Auth**: `DefaultAzureCredential` (Entra ID, no keys)
- **Consistency**: Session — read-your-own-writes
- **RU Budget**: 400 RU/s shared (Autoscale) for dev/test
- **Local Dev**: In-memory mock dictionary (no Emulator)

**Data Flow:**
```
User Request
    │
    ├── Auth/Profile/Vocab/Progress/Streaks → PostgreSQL (SQLAlchemy async)
    │
    ├── Chat/Voice conversation             → Cosmos DB (conversations)
    ├── Drama content lookup                → Cosmos DB (drama_content)
    ├── Learning analytics events           → Cosmos DB (learning_events)
    │
    ├── Thread IDs, Rate limits             → Redis Cache
    ├── Verification codes (TTL 5min)       → Redis Cache (memory fallback)
    └── Study session minutes               → Redis Cache
```

### 6. Redis Cache Strategy

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `thread:{user_id}` | 24h | Current conversation thread |
| `ctx:{thread_id}` | 1h | Conversation context summary |
| `study:{user_id}:today` | 24h | Daily study minutes counter |
| `streak:{user_id}` | 48h | Consecutive study days |
| `rl:{user_id}` | 60s | Rate limiting counter |
| `verify:{email}` | 5min | Email verification code |
| `verify_rate:{email}` | 60s | Code send rate limit |

**Fallback modes**: Azure Redis (SSL) → fakeredis (local dev) → memory dict (last resort)
**Diagnostics**: `get_diagnostics()` returns auth_mode, url_scheme, masked_url, last_error

### 7. Voice Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| **TTS Voice** | `ko-KR-SunHiNeural` | Korean female, warm, professional |
| **STT Languages** | `ko-KR`, `en-US`, `zh-CN` | Parallel auto-detect |
| **Audio Input** | 16kHz mono WAV | STT optimal format |
| **Audio Output** | MP3 128kbps | TTS output (compact) |
| **SSML** | Prosody tuning | Natural speech patterns |
| **ffmpeg** | System dep (startup.sh) | Non-WAV audio conversion |
| **Fallback** | Pure Python resample | When ffmpeg unavailable |

### 8. Email Verification Architecture

```
Client                    Server                    Azure
  │                          │                         │
  │ POST /api/auth/send-code │                         │
  ├─────────────────────────►│                         │
  │                          │ Rate check (Redis)      │
  │                          │ Generate 6-digit code   │
  │                          │ Store in Redis (5min)   │
  │                          │                         │
  │                          │ ACS REST API            │
  │                          │ (HMAC-SHA256 auth)      │
  │                          ├────────────────────────►│
  │                          │                         │ Send email
  │                          │◄────────────────────────┤
  │ {success: true}          │                         │
  │◄─────────────────────────┤                         │
  │                          │                         │
  │ POST /api/auth/register  │                         │
  │ {email, password, code}  │                         │
  ├─────────────────────────►│                         │
  │                          │ Verify code (Redis)     │
  │                          │ bcrypt hash password    │
  │                          │ Create user (PostgreSQL)│
  │                          │ Issue JWT               │
  │ {access_token, user_id}  │                         │
  │◄─────────────────────────┤                         │
```

### 9. Admin Dashboard Architecture

- **Authentication**: `X-Admin-Key` header verified against `JWT_SECRET`
- **Data Source**: Direct PostgreSQL aggregate queries (no separate analytics DB)
- **Frontend**: Single HTML page (`admin_dashboard.html`) with sidebar navigation, charts, KPI grid
- **Endpoints**: 4 REST APIs (overview, signups/trend, dau/trend, users)

### 10. Deployment

- **Azure App Service**: B1 Linux, Python 3.12, VNet integrated
- **Build**: Oryx (SCM_DO_BUILD_DURING_DEPLOYMENT=true)
- **Startup**: `startup.sh` → install zstd+ffmpeg → extract deps → uvicorn --workers 2
- **VNet Integration**: Private endpoints for PostgreSQL + Redis + Cosmos DB
- **Managed Identity**: `DefaultAzureCredential` for AI Foundry, Speech, Cosmos
- **Defender**: Microsoft Defender for App Service enabled (Standard tier)
- **DNS**: Private DNS zones for all Azure PaaS services
