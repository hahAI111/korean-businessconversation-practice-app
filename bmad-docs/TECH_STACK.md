---
stepsCompleted: [runtime, services, conventions, frontend, structure, review]
inputDocuments: [PRD.md, ARCHITECTURE.md, codebase-scan]
workflowType: 'architecture'
bmadAgent: 'Architect Winston'
bmadVersion: '6.2.2'
lastUpdated: '2026-03-27'
---

# Tech Stack & Conventions
## Korean Biz Coach — Technical Standards

> **BMAD Agent**: Architect Winston (System Architect) | **Phase**: 2-Solutioning
> **Status**: Living Document — reflects current production state

### Language & Runtime
- **Python 3.12** (App Service production, Oryx build)
- **FastAPI** (async ASGI framework)
- **Uvicorn** (ASGI server, 2 workers)
- **SQLAlchemy 2.0** (async, mapped_column, DeclarativeBase)
- **Pydantic v2** (Settings + request/response validation)
- **asyncpg** (PostgreSQL async driver)
- **aioredis** (Redis async driver)
- **azure-cosmos** (Cosmos DB async SDK)

### Azure Services (All Entra ID / No Keys — unless noted)

| Service | Auth Method | SDK/API | Usage |
|---------|------------|---------|-------|
| **AI Foundry** | DefaultAzureCredential → Bearer | `azure-ai-projects` (Responses API) | GPT-5-nano + MCP tools |
| **Speech Service** | DefaultAzureCredential → Bearer | REST API (no SDK) | STT, TTS (SSML), Pronunciation |
| **PostgreSQL** | Password in connection string | `asyncpg` via SQLAlchemy | Relational data (6 tables) |
| **Cosmos DB** | DefaultAzureCredential (Entra ID) | `azure-cosmos` async | Document data (3 containers) |
| **Redis Cache** | Access key in URL (SSL) | `aioredis` / `fakeredis` | Cache, sessions, verification codes |
| **App Service** | Managed Identity | — | Hosting (B1 Linux) |
| **Communication Services** | HMAC-SHA256 (connection string) | REST API | Email verification codes |

### System Dependencies (installed at startup)
- **zstd** — Dependency decompression
- **ffmpeg** — Audio format conversion (non-WAV → WAV for STT)

### Code Conventions
- **Language**: Chinese comments for documentation (target audience: Chinese developers)
- **Type hints**: Everywhere (function signatures, return types)
- **Async/await**: All I/O operations (database, HTTP, cache, cosmos)
- **Logging**: Python `logger` (never `print`)
- **Sensitive data**: Masked in logs (`_mask_url()` for Redis URLs)
- **Error handling**: Graceful fallbacks (Redis→memory, Cosmos→mock, ffmpeg→Python resample)
- **Auth pattern**: `get_current_user_id` dependency for JWT, `_verify_token` for WebSocket
- **Background tasks**: `asyncio.create_task()` for fire-and-forget saves (conversation, events, study session)

### Frontend
- **Vanilla JS** (no framework — no React/Vue/Angular)
- **MSAL.js** (Microsoft Entra ID login)
- **CSS custom properties** for theming (gold/navy palette)
- **Dark theme** with responsive design (desktop + mobile)
- **PWA**: Service Worker + Web App Manifest + offline.html fallback
- **6 pages**: index (auth), chat, vocab, progress, admin_dashboard, offline

### Project Structure
```
korean-biz-agent/
├── bmad-docs/          # BMAD planning artifacts (PRD, ARCH, STORIES, TECH_STACK)
├── _bmad/              # BMAD framework (v6.2.2, 9 agents, 44+ skills)
├── _bmad-output/       # BMAD output artifacts (specs, implementation)
├── docs/               # Project documentation (10 docs)
├── app/                # FastAPI application
│   ├── core/           # Config, DB, Cosmos, Redis, Auth (5 modules)
│   ├── api/            # Route handlers (7 routers, 25+ endpoints)
│   ├── models/         # SQLAlchemy models (6 tables, 2 enums)
│   ├── schemas/        # Pydantic schemas (15+ models)
│   ├── services/       # Business logic (5 services)
│   └── utils/          # Utility modules
├── mcp_server/         # FastMCP teaching tools (9 tools)
├── data/               # Content data (business_korean.json)
├── static/             # Frontend files (6 HTML + JS + CSS + PWA)
├── alembic/            # Database migrations
├── scripts/            # Admin scripts (create_agents.py)
└── tests/              # Test suite
```

### Key Dependencies (requirements.txt)
| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | Web framework + ASGI server |
| `sqlalchemy[asyncio]` + `asyncpg` | PostgreSQL ORM |
| `azure-ai-projects` | AI Foundry Responses API |
| `azure-cosmos` | Cosmos DB NoSQL |
| `azure-identity` | DefaultAzureCredential |
| `aioredis` | Redis async |
| `bcrypt` | Password hashing |
| `pyjwt` + `cryptography` | JWT (HS256 + RS256 JWKS) |
| `mcp[cli]` | FastMCP tools server |
| `pydantic-settings` | Environment configuration |
| `pydub` | Audio processing (with ffmpeg) |
| `msal` | Microsoft auth (server-side) |
