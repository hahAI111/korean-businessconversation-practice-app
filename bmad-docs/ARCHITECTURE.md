# Architecture Document
## Korean Biz Coach — System Architecture

### 1. System Context

```
Users (Web Browser)
        │
        ▼
Azure App Service (FastAPI)
   ├── REST API (text chat, vocab, progress, auth)
   ├── WebSocket (real-time voice conversation)
   └── Static Files (SPA frontend)
        │
        ├──► Azure AI Foundry (GPT model + MCP tools)
        ├──► Azure Speech Service (STT / TTS / Assessment)
        ├──► Azure PostgreSQL (relational: users, lessons, progress)
        ├──► Azure Cosmos DB (documents: conversations, drama, events)
        └──► Azure Redis Cache (sessions, rate-limit, context)
```

### 2. Authentication — AAD/Entra ID Only (No Keys)

All Azure service access uses `DefaultAzureCredential`:
- **AI Foundry**: Managed Identity → `AzureOpenAI(credential=get_bearer_token_provider(..., "cognitiveservices.azure.com/.default"))`
- **Speech**: Managed Identity → Bearer token for REST API
- **PostgreSQL**: Connection string with password (VNet private endpoint)
- **Redis**: Access key via connection string (VNet private endpoint)

User authentication: JWT tokens issued by the app (register/login).

### 3. Component Architecture

```
app/
├── main.py                 # FastAPI app, lifespan, CORS, routes
├── core/
│   ├── config.py           # Pydantic Settings (.env)
│   ├── database.py         # Async SQLAlchemy engine (PostgreSQL)
│   ├── cosmos.py           # Azure Cosmos DB async client
│   ├── redis.py            # Redis client (Azure/FakeRedis)
│   └── auth.py             # JWT create/verify
├── api/
│   ├── auth.py             # Register/Login/Profile
│   ├── chat.py             # Text chat + voice chat endpoints
│   ├── voice_ws.py         # WebSocket real-time voice
│   ├── pronunciation.py    # Pronunciation assessment
│   ├── progress.py         # Learning progress dashboard
│   └── vocab.py            # Vocabulary CRUD
├── models/
│   └── models.py           # SQLAlchemy ORM models
├── schemas/
│   └── schemas.py          # Pydantic request/response
├── services/
│   ├── agent_service.py    # Azure AI Foundry Agent lifecycle
│   ├── speech_service.py   # Azure Speech STT/TTS/Assessment
│   ├── cosmos_service.py   # Cosmos DB CRUD operations
│   └── cache_service.py    # Redis caching layer
mcp_server/
│   └── server.py           # 9 FastMCP teaching tools
data/
│   └── business_korean.json # Teaching content (vocab, grammar, dramas)
static/
│   ├── index.html          # Login/Register
│   ├── chat.html           # Main chat + voice UI
│   ├── vocab.html          # Vocabulary page
│   ├── progress.html       # Progress dashboard
│   ├── style.css           # Global styles
│   └── app.js              # Shared JS (API, Auth, Toast, etc.)
```

### 4. Real-time Voice Architecture

```
Browser                    Server                    Azure
  │                          │                         │
  │ 1. WS connect           │                         │
  ├─────────────────────────►│                         │
  │                          │                         │
  │ 2. Audio chunk (binary)  │                         │
  ├─────────────────────────►│                         │
  │                          │ 3. STT (REST)           │
  │                          ├────────────────────────►│
  │                          │ 4. Transcript           │
  │                          │◄────────────────────────┤
  │ 5. {transcript}          │                         │
  │◄─────────────────────────┤                         │
  │                          │ 6. AI Agent chat        │
  │                          ├────────────────────────►│
  │                          │ 7. AI reply             │
  │                          │◄────────────────────────┤
  │ 8. {reply_text}          │                         │
  │◄─────────────────────────┤                         │
  │                          │ 9. TTS (REST)           │
  │                          ├────────────────────────►│
  │                          │ 10. Audio bytes         │
  │                          │◄────────────────────────┤
  │ 11. Audio (binary)       │                         │
  │◄─────────────────────────┤                         │
```

### 5. Dual Database Architecture (双数据库架构)

#### 5.1 PostgreSQL — Relational Data (关系型数据)

| Table | Purpose |
|-------|--------|
| users | User accounts, Korean level, settings |
| lessons | Teaching content by category |
| learning_progress | User ↔ Lesson completion/scores |
| vocab_book | Personal vocabulary with mastery |
| study_streaks | Daily activity tracking |

#### 5.2 Cosmos DB — Document Data (文档型数据)

| Container | Partition Key | Purpose |
|-----------|--------------|--------|
| conversations | `/user_id` | Chat history — nested messages array, high write volume |
| drama_content | `/drama_id` | K-drama dialogues — rich nested scenes, cultural notes, flexible schema |
| learning_events | `/user_id` | Analytics event stream — append-only, time-series learning activity |

**Cosmos DB Design Decisions:**
- **API**: NoSQL (SQL API) — familiar SQL-like queries, best SDK support
- **Auth**: `DefaultAzureCredential` (Entra ID, no keys)
- **Consistency**: Session (default) — read-your-own-writes within a session
- **RU Budget**: 400 RU/s shared (Autoscale) for dev/test
- **Local Dev**: In-memory mock dictionary (no Emulator needed)

**Data Flow (数据流向):**
```
User Request
    │
    ├── Auth/Profile/Vocab/Progress → PostgreSQL (SQLAlchemy)
    │
    ├── Chat/Voice conversation     → Cosmos DB (conversations)
    ├── Drama content lookup         → Cosmos DB (drama_content)
    └── Learning analytics           → Cosmos DB (learning_events)
```

### 6. Redis Cache Strategy

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `thread:{user_id}` | 24h | Current conversation thread |
| `ctx:{thread_id}` | 1h | Conversation context summary |
| `study:{user_id}:today` | 24h | Daily study minutes |
| `streak:{user_id}` | 48h | Consecutive study days |
| `rl:{user_id}` | 60s | Rate limiting counter |

### 7. Voice Configuration

- **TTS Voice**: `ko-KR-SunHiNeural` (Korean female, warm, professional)
- **STT Language**: `ko-KR` (Korean), with auto-detect fallback
- **Audio Format**: 16kHz mono WAV (STT input), MP3 128kbps (TTS output)
- **WebSocket**: Binary frames for audio, JSON text frames for metadata

### 8. Deployment

- **Azure App Service**: B1 Linux, Python 3.12
- **Build**: Oryx (SCM_DO_BUILD_DURING_DEPLOYMENT=true)
- **Startup**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`
- **VNet Integration**: Private endpoints for PostgreSQL + Redis + Cosmos DB
