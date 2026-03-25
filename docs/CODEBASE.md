# 📂 Complete Codebase Guide / 전체 코드베이스 가이드

> Every file and folder explained — what it does, how it connects, and why it exists.
>
> 모든 파일과 폴더 설명 — 무엇을 하는지, 어떻게 연결되는지, 왜 존재하는지.

---

## Table of Contents / 목차

1. [Root Files / 루트 파일](#1-root-files--루트-파일)
2. [app/ — Backend Application / 백엔드 애플리케이션](#2-app--backend-application--백엔드-애플리케이션)
3. [mcp_server/ — Teaching Tools / 교육 도구](#3-mcp_server--teaching-tools--교육-도구)
4. [data/ — Teaching Content / 교육 콘텐츠](#4-data--teaching-content--교육-콘텐츠)
5. [static/ — Frontend & PWA / 프론트엔드 & PWA](#5-static--frontend--pwa--프론트엔드--pwa)
6. [alembic/ — Database Migrations / DB 마이그레이션](#6-alembic--database-migrations--db-마이그레이션)
7. [_bmad/ — BMAD Framework / BMAD 프레임워크](#7-_bmad--bmad-framework--bmad-프레임워크)
8. [bmad-docs/ — BMAD Documents / BMAD 문서](#8-bmad-docs--bmad-documents--bmad-문서)
9. [scripts/ — Utility Scripts / 유틸리티 스크립트](#9-scripts--utility-scripts--유틸리티-스크립트)
10. [tests/ — Test Suite / 테스트](#10-tests--test-suite--테스트)

---

## 1. Root Files / 루트 파일

| File / 파일 | Purpose / 용도 |
|---|---|
| `requirements.txt` | Python dependencies (30+ packages: FastAPI, SQLAlchemy, openai, azure-identity, httpx, etc.) / Python 의존성 |
| `startup.sh` | Azure App Service startup script — activates `antenv` virtual environment, launches `uvicorn --workers 2` / Azure 시작 스크립트 |
| `Dockerfile` | Container build — Python 3.12-slim base, pip install, uvicorn entry / 컨테이너 빌드 |
| `docker-compose.yml` | Local container orchestration (connects to Azure resources) / 로컬 컨테이너 오케스트레이션 |
| `alembic.ini` | Alembic migration configuration / Alembic 마이그레이션 설정 |
| `.env` | Production secrets (NOT committed to git) / 프로덕션 시크릿 (git에 커밋 안 됨) |
| `.env.example` | Template showing all required environment variables / 필수 환경 변수 템플릿 |
| `.env.local` | Local dev overrides (SQLite + fakeredis) / 로컬 개발 오버라이드 |
| `.gitignore` | Git exclusion rules (.env, __pycache__, deploy zips, etc.) / Git 제외 규칙 |
| `check_deploy.py` | Pre-deployment validation script / 배포 전 검증 스크립트 |
| `make_zip.py` | Build zip for Azure deployment / Azure 배포용 zip 빌드 |

---

## 2. app/ — Backend Application / 백엔드 애플리케이션

The heart of the project. A FastAPI async application organized in clean layers.

프로젝트의 핵심. 깔끔한 계층 구조로 구성된 FastAPI 비동기 애플리케이션.

```
app/
├── __init__.py
├── main.py             ← Entry point / 진입점
├── core/               ← Infrastructure layer / 인프라 계층
│   ├── config.py
│   ├── database.py
│   ├── cosmos.py
│   ├── redis.py
│   └── auth.py
├── api/                ← Route handlers / 라우트 핸들러
│   ├── auth.py
│   ├── chat.py
│   ├── voice_ws.py
│   ├── pronunciation.py
│   ├── progress.py
│   └── vocab.py
├── models/             ← Database models / 데이터베이스 모델
│   └── models.py
├── schemas/            ← Request/Response types / 요청/응답 타입
│   └── schemas.py
├── services/           ← Business logic / 비즈니스 로직
│   ├── agent_service.py
│   ├── speech_service.py
│   ├── cache_service.py
│   └── cosmos_service.py
└── utils/
    └── __init__.py
```

### 2.1 main.py — Application Entry Point / 앱 진입점

**What it does / 하는 일**:
- **Lifespan manager**: Initializes database tables, Cosmos DB client, and cleanly shuts down all services on exit / 라이프스팬 관리자: DB 테이블 생성, Cosmos DB 클라이언트 초기화, 종료 시 모든 서비스 정리
- **CORS middleware**: Allows all origins for mobile/PWA compatibility / CORS 미들웨어: 모바일/PWA 호환을 위해 모든 출처 허용
- **Route mounting**: Registers 6 API routers at their paths / 라우트 마운트: 6개 API 라우터를 경로에 등록
- **MCP server mount**: Mounts FastMCP teaching tools at `/mcp` / MCP 서버 마운트: 교육 도구를 `/mcp`에 마운트
- **PWA support**: Serves `manifest.json` and `service-worker.js` from root path (required by PWA spec) / PWA 지원: 루트 경로에서 manifest.json과 service-worker.js 제공
- **Static files**: Serves frontend from `/static/` / 정적 파일: `/static/`에서 프론트엔드 제공
- **Health check**: `GET /health` returns service status including Cosmos DB connection state / 상태 확인: Cosmos DB 연결 상태 포함 서비스 상태 반환

```python
# Startup flow / 시작 흐름:
async def lifespan(app):
    # 1. Create all database tables / 모든 DB 테이블 생성
    # 2. Initialize Cosmos DB (falls back to mock if unavailable) / Cosmos DB 초기화
    yield
    # 3. Cleanup: close agent, cosmos, redis / 정리: 에이전트, cosmos, redis 종료
```

### 2.2 core/ — Infrastructure Layer / 인프라 계층

#### config.py — Application Configuration / 앱 설정

**Pydantic Settings** that auto-loads from `.env` and `.env.local` files.

`.env`와 `.env.local` 파일에서 자동 로드하는 **Pydantic Settings**.

| Setting Group / 설정 그룹 | Variables / 변수 | Description / 설명 |
|---|---|---|
| Azure AI Foundry | `AZURE_AI_ENDPOINT`, `MODEL_DEPLOYMENT` | GPT endpoint and model name / GPT 엔드포인트와 모델명 |
| Agent Names / 에이전트명 | `TEXT_AGENT_NAME`, `VOICE_AGENT_NAME` | Portal-configured agent names / 포털 설정 에이전트명 |
| Azure Speech / 음성 | `AZURE_SPEECH_REGION`, `AZURE_SPEECH_RESOURCE_ENDPOINT`, `AZURE_SPEECH_RESOURCE_ID` | Speech REST API connection / 음성 REST API 연결 |
| Cosmos DB | `COSMOS_ENDPOINT`, `COSMOS_DATABASE` | Document database (empty = mock mode) / 문서 DB (비우면 mock 모드) |
| PostgreSQL | `DATABASE_URL` | Async connection string / 비동기 연결 문자열 |
| Redis | `REDIS_URL` | Cache connection (`fake` = fakeredis) / 캐시 연결 |
| JWT Auth / JWT 인증 | `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` | Token signing config / 토큰 서명 설정 |

**Key design / 핵심 설계**: `.env.local` overrides `.env`, so local development uses SQLite + fakeredis without touching production settings.

`.env.local`이 `.env`를 오버라이드하므로, 로컬 개발 시 프로덕션 설정을 건드리지 않고 SQLite + fakeredis를 사용합니다.

#### database.py — Async Database Engine / 비동기 DB 엔진

- Creates `AsyncEngine` via `create_async_engine(DATABASE_URL)`
- Supports both PostgreSQL (`asyncpg`) and SQLite (`aiosqlite`)
- `AsyncSessionLocal` factory for request-scoped sessions
- `init_db()` creates all tables using `Base.metadata.create_all`

비동기 엔진 생성, PostgreSQL과 SQLite 모두 지원, 요청 범위 세션 팩토리 제공.

#### cosmos.py — Cosmos DB Client / Cosmos DB 클라이언트

- Async client using `azure-cosmos` SDK with `DefaultAzureCredential` (Entra ID, no API key)
- **3 containers** with partition keys:
  - `conversations` (partition: `/user_id`) — Chat history / 대화 기록
  - `drama_content` (partition: `/drama_id`) — K-drama teaching material / 드라마 교재
  - `learning_events` (partition: `/user_id`) — Learning activity log / 학습 활동 로그
- **Auto-fallback**: If `COSMOS_ENDPOINT` is empty or connection fails → in-memory mock (dict-based) / 자동 대체: 연결 실패 시 메모리 mock

#### redis.py — Redis Cache Client / Redis 캐시 클라이언트

- **3 modes / 3가지 모드**:
  1. `REDIS_URL=fake` → `fakeredis` (local development / 로컬 개발)
  2. `REDIS_URL=rediss://...` → Real Azure Redis with SSL / 실제 Azure Redis (SSL)
  3. Connection failure → In-memory dict fallback (automatic) / 연결 실패 → 메모리 dict 대체
- `_auth_mode` tracks current mode: `"access-key"` / `"fake"` / `"memory-fallback"` / `"not-connected"`
- Status check via `GET /api/chat/redis-check` / 상태 확인

#### auth.py — JWT Authentication / JWT 인증

- `create_access_token(user_id)` → Signs JWT with HS256, 24h expiry / JWT 생성, 24시간 만료
- `_verify_token(token)` → Decodes and validates JWT / JWT 디코드 및 검증
- `get_current_user_id()` → FastAPI `Depends()` for protected endpoints / 보호 엔드포인트용 의존성
- Used by both HTTP (`Authorization: Bearer`) and WebSocket (first message `{"type":"start","token":"..."}`)

HTTP와 WebSocket 모두에서 사용됩니다.

### 2.3 api/ — Route Handlers / 라우트 핸들러

#### auth.py — User Registration & Login / 사용자 등록 & 로그인

| Endpoint / 엔드포인트 | Method | Auth | What it does / 하는 일 |
|---|---|---|---|
| `/api/auth/register` | POST | ❌ | Create user (bcrypt hash password), return JWT / 사용자 생성, JWT 반환 |
| `/api/auth/login` | POST | ❌ | Verify credentials, return JWT / 인증 정보 확인, JWT 반환 |
| `/api/auth/profile` | GET | ✅ | Return user profile data / 사용자 프로필 반환 |

#### chat.py — AI Text Chat / AI 텍스트 대화

| Endpoint / 엔드포인트 | Method | What it does / 하는 일 |
|---|---|---|
| `/api/chat` | POST | Main text chat — rate limit → get/create thread → call GPT agent → return reply / 메인 텍스트 대화 |
| `/api/chat/tts` | POST | Convert text to speech (strips markdown → Azure TTS → base64 MP3) / 텍스트를 음성으로 변환 |
| `/api/chat/new-thread` | POST | Create new conversation thread / 새 대화 스레드 생성 |
| `/api/chat/history` | GET | List user's conversation history / 대화 기록 목록 |
| `/api/chat/history/{id}` | GET/DELETE | Load or delete specific conversation / 특정 대화 로드/삭제 |
| `/api/chat/redis-check` | GET | Redis connection diagnostic / Redis 연결 진단 |
| `/api/chat/speech-check` | GET | Speech service diagnostic / 음성 서비스 진단 |
| `/api/chat/agent-check` | GET | Agent service diagnostic / 에이전트 서비스 진단 |

**Key pattern / 핵심 패턴**: Fire-and-forget background tasks for non-critical operations (study time logging, conversation saving) to keep response fast.

비핵심 작업(학습 시간 기록, 대화 저장)은 fire-and-forget 백그라운드로 처리하여 응답 속도를 유지합니다.

#### voice_ws.py — Real-time Voice WebSocket / 실시간 음성 WebSocket

The most complex handler. Manages a full-duplex voice conversation over WebSocket.

가장 복잡한 핸들러. WebSocket을 통한 전이중 음성 대화를 관리합니다.

**WebSocket Protocol / WebSocket 프로토콜**:
```
Client → Server:
  1. JSON: {"type":"start", "token":"jwt-token", "language":"auto"}  ← Auth / 인증
  2. Binary frames: WAV audio chunks                                  ← Voice data / 음성 데이터
  3. JSON: {"type":"end_audio"}                                       ← End of speech / 발화 종료
  4. JSON: {"type":"text", "message":"..."}                           ← Text input / 텍스트 입력
  5. JSON: {"type":"new_thread"}                                      ← New conversation / 새 대화
  6. JSON: {"type":"set_language", "language":"ko-KR"}                ← Change language / 언어 변경

Server → Client:
  1. JSON: {"type":"ready", "thread_id":"...", "message":"..."}       ← Connected / 연결됨
  2. JSON: {"type":"status", "status":"processing|speaking|ready"}    ← Status updates / 상태
  3. JSON: {"type":"transcript", "text":"..."}                        ← STT result / 음성인식 결과
  4. JSON: {"type":"reply", "text":"...", "thread_id":"..."}          ← AI response / AI 응답
  5. Binary: MP3 audio                                                ← TTS audio / TTS 오디오
  6. JSON: {"type":"error", "message":"..."}                          ← Error / 오류
```

**Processing pipeline / 처리 파이프라인**:
```
Audio frames → Collect → WAV 16kHz conversion → Azure STT (auto-detect language)
  → Recognized text → GPT Agent (VOICE_INSTRUCTIONS) → AI reply text
    → Azure TTS (SunHiNeural SSML) → MP3 audio → Send to client
```

#### pronunciation.py — Pronunciation Assessment / 발음 평가

Single endpoint: `POST /api/pronunciation` — sends audio + reference text to Azure Speech Pronunciation Assessment API, returns word-level accuracy scores (100-point scale).

단일 엔드포인트: 오디오 + 참조 텍스트를 Azure Speech 발음 평가 API에 전송, 단어별 정확도 점수 반환 (100점 만점).

#### progress.py — Learning Dashboard / 학습 대시보드

| Endpoint / 엔드포인트 | What it does / 하는 일 |
|---|---|
| `GET /api/progress` | Overall stats: total lessons, completed, streak days, study minutes, avg pronunciation / 전체 통계 |
| `GET /api/lessons` | List lessons filtered by category/level / 카테고리/레벨별 강의 목록 |
| `GET /api/streaks?days=30` | Daily study history for chart display / 차트용 일별 학습 기록 |
| `POST /api/progress/checkin` | Daily check-in (打卡) — updates streak / 일일 체크인 — 연속 학습 업데이트 |

#### vocab.py — Vocabulary Book CRUD / 단어장 CRUD

| Endpoint / 엔드포인트 | What it does / 하는 일 |
|---|---|
| `GET /api/vocab` | List vocabulary items (filter by mastered/tag) / 단어 목록 (마스터/태그 필터) |
| `POST /api/vocab` | Add new word (korean, meaning, example, tags) / 새 단어 추가 |
| `PATCH /api/vocab/{id}/master` | Toggle mastered status / 마스터 상태 전환 |
| `PUT /api/vocab/{id}` | Update word details / 단어 정보 수정 |
| `DELETE /api/vocab/{id}` | Remove from vocabulary book / 단어장에서 삭제 |

### 2.4 models/models.py — Database Schema / 데이터베이스 스키마

> Full schema details in [docs/DATABASE.md](DATABASE.md)
>
> 전체 스키마 상세 내용은 [docs/DATABASE.md](DATABASE.md) 참조

6 SQLAlchemy ORM models + 2 enums. Uses `DeclarativeBase` (SQLAlchemy 2.0 style) with JSON/JSONB columns for flexible data.

6개 SQLAlchemy ORM 모델 + 2개 열거형. 유연한 데이터를 위해 JSON/JSONB 컬럼과 함께 DeclarativeBase (SQLAlchemy 2.0 스타일) 사용.

### 2.5 schemas/schemas.py — Pydantic Models / Pydantic 모델

15+ Pydantic models for request validation and response serialization:

요청 검증 및 응답 직렬화를 위한 15개 이상의 Pydantic 모델:

| Group / 그룹 | Models / 모델 | Purpose / 용도 |
|---|---|---|
| Auth / 인증 | `UserRegister`, `UserLogin`, `TokenResponse`, `UserProfile` | Registration, login, profile / 회원가입, 로그인, 프로필 |
| Chat / 대화 | `ChatRequest`, `ChatResponse`, `TtsRequest` | Text chat I/O / 텍스트 대화 입출력 |
| Voice / 음성 | `VoiceChatRequest`, `VoiceChatResponse` | Voice chat REST endpoint / 음성 대화 REST |
| Pronunciation / 발음 | `PronunciationRequest`, `PronunciationResult` | Pronunciation scoring / 발음 평가 |
| Progress / 진도 | `ProgressResponse`, `StudyStreakResponse` | Learning dashboard data / 학습 대시보드 데이터 |
| Vocab / 단어장 | `VocabAddRequest`, `VocabResponse` | Vocabulary CRUD / 단어장 CRUD |
| Lessons / 강의 | `LessonSummary` | Lesson listing / 강의 목록 |

### 2.6 services/ — Business Logic Layer / 비즈니스 로직 계층

> Detailed in [docs/AI_ENGINE.md](AI_ENGINE.md) and [docs/DATABASE.md](DATABASE.md)
>
> 상세 내용은 [docs/AI_ENGINE.md](AI_ENGINE.md)와 [docs/DATABASE.md](DATABASE.md) 참조

| Service / 서비스 | File / 파일 | Role / 역할 |
|---|---|---|
| **AgentService** | `agent_service.py` | GPT agent interaction via Azure AI Foundry Responses API / GPT 에이전트 상호작용 |
| **SpeechService** | `speech_service.py` | Azure Speech REST API for STT, TTS, pronunciation / 음성인식, 합성, 발음평가 |
| **CacheService** | `cache_service.py` | Redis cache wrapper with memory fallback / Redis 캐시 래퍼 + 메모리 대체 |
| **CosmosService** | `cosmos_service.py` | Cosmos DB CRUD for conversations, drama, events / Cosmos DB CRUD |

---

## 3. mcp_server/ — Teaching Tools / 교육 도구

**MCP (Model Context Protocol)** provides 9 specialized tools that the GPT agent can call during conversations to access structured teaching data.

**MCP (Model Context Protocol)**는 GPT 에이전트가 대화 중 구조화된 교육 데이터에 접근하기 위해 호출할 수 있는 9개의 전문 도구를 제공합니다.

| # | Tool / 도구 | What it does / 하는 일 |
|---|---|---|
| 1 | `lookup_vocabulary` | Search 50+ business Korean terms by korean/chinese/english/romanization / 비즈니스 한국어 용어 검색 |
| 2 | `get_grammar_pattern` | Query 20+ grammar rules with explanation and examples / 문법 규칙 조회 |
| 3 | `generate_business_scenario` | Create conversation frameworks for 6 situations (meeting, negotiation, phone, presentation, networking, interview) / 6가지 상황 대화 프레임워크 생성 |
| 4 | `get_email_template` | Business email templates (meeting request, thank you, apology, inquiry, introduction, follow-up) / 비즈니스 이메일 템플릿 |
| 5 | `check_formality` | Verify 경어 (honorific) level appropriateness for context / 경어 수준 적절성 확인 |
| 6 | `quiz_me` | Random quiz (vocabulary, grammar, formality, email, conversation) / 랜덤 퀴즈 |
| 7 | `get_drama_dialogue` | Real K-drama workplace dialogues from 미생, 스타트업, 이태원클라쓰, 김과장, 비밀의숲 / 한국 드라마 직장 대화 |
| 8 | `get_sentence_endings` | 45+ 어미/연결어미 reference (-는데, -거든요, -잖아요, -더라고요, etc.) / 어미 참조 |
| 9 | `practice_conversation` | Interactive role-play conversation scenarios / 대화형 롤플레이 시나리오 |

**Data source / 데이터 소스**: All tools read from `data/business_korean.json`

**Mounting / 마운트**: Mounted at `/mcp` in `main.py`, accessible to the Azure AI Foundry agent via `agent_reference`

---

## 4. data/ — Teaching Content / 교육 콘텐츠

### business_korean.json

A comprehensive Korean business curriculum in JSON format (~27KB):

JSON 형식의 종합 한국어 비즈니스 커리큘럼 (~27KB):

| Section / 섹션 | Content / 내용 | Size / 규모 |
|---|---|---|
| `vocabulary[]` | Business terms with formal/informal, romanization, meaning / 비즈니스 용어 | 50+ entries / 50개 이상 |
| `grammar_patterns[]` | Grammar rules with explanation and examples / 문법 규칙 | 20+ patterns / 20개 이상 |
| `scenarios{}` | 6 business conversation frameworks / 6가지 비즈니스 대화 프레임워크 | 6 types / 6가지 유형 |
| `email_templates{}` | Business email templates / 비즈니스 이메일 템플릿 | 6 templates / 6개 템플릿 |
| `sentence_endings[]` | 어미 and 연결어미 with usage patterns / 어미와 연결어미 | 45+ entries / 45개 이상 |
| `drama_dialogues[]` | K-drama workplace scenes / 한국 드라마 직장 장면 | 5+ dramas / 5개 이상 드라마 |
| `quizzes[]` | Random quiz data / 랜덤 퀴즈 데이터 | Multiple types / 다양한 유형 |

---

## 5. static/ — Frontend & PWA / 프론트엔드 & PWA

Zero-dependency vanilla HTML/CSS/JS with PWA support. Dark theme with gold (#c9a96e) and navy (#0b0e13) color scheme.

의존성 제로 바닐라 HTML/CSS/JS + PWA 지원. 골드(#c9a96e)와 네이비(#0b0e13) 색상의 다크 테마.

| File / 파일 | Page / 페이지 | Features / 기능 |
|---|---|---|
| `index.html` | Login / Register / 로그인 / 회원가입 | Email + password auth, redirect to chat on success / 이메일+비밀번호 인증 |
| `chat.html` | Main Chat / 메인 대화 | Text chat, voice recording (WebSocket), TTS playback, thread management, markdown rendering / 텍스트 대화, 음성 녹음, TTS 재생 |
| `vocab.html` | Vocabulary / 단어장 | Add/edit/delete words, tag filtering, mastery toggle / 단어 추가/편집/삭제, 태그 필터, 마스터 전환 |
| `progress.html` | Dashboard / 대시보드 | Study time chart (30-day bar), streak calendar, check-in button / 학습 시간 차트, 연속 학습 캘린더, 체크인 버튼 |
| `app.js` | Shared Utils / 공유 유틸 | Auth helpers (token, userId, logout), API wrapper (fetch with JWT), toast notifications / 인증 헬퍼, API 래퍼, 토스트 알림 |
| `style.css` | Global Styles / 글로벌 스타일 | CSS custom properties, responsive breakpoints, dark theme / CSS 변수, 반응형, 다크 테마 |
| `manifest.json` | PWA Manifest / PWA 매니페스트 | App name, icons, theme color, display mode / 앱 이름, 아이콘, 테마 색상 |
| `service-worker.js` | Service Worker / 서비스 워커 | Cache strategy (network-first for API, cache-first for assets), offline fallback / 캐시 전략, 오프라인 대체 |
| `offline.html` | Offline Page / 오프라인 페이지 | Shown when network unavailable / 네트워크 불가 시 표시 |
| `icons/` | PWA Icons / PWA 아이콘 | 192x192, 512x512, apple-touch-icon / PWA 아이콘 세트 |

---

## 6. alembic/ — Database Migrations / DB 마이그레이션

Standard Alembic setup for PostgreSQL schema migrations.

PostgreSQL 스키마 마이그레이션을 위한 표준 Alembic 설정.

| File / 파일 | Purpose / 용도 |
|---|---|
| `env.py` | Migration environment — loads `DATABASE_URL` from config / 마이그레이션 환경 |
| `script.py.mako` | Migration template / 마이그레이션 템플릿 |
| `versions/` | Migration scripts (currently uses `create_all` for initial setup) / 마이그레이션 스크립트 |

---

## 7. _bmad/ — BMAD Framework / BMAD 프레임워크

> Full explanation in [docs/BMAD.md](BMAD.md)
>
> 상세 내용은 [docs/BMAD.md](BMAD.md) 참조

BMAD (Build Measure Analyze Decide) v6.2 development methodology framework. NOT runtime code — it's a structured agile process used to plan and build the project.

BMAD v6.2 개발 방법론 프레임워크. 런타임 코드가 아님 — 프로젝트를 계획하고 구축하는 데 사용되는 구조화된 애자일 프로세스.

```
_bmad/
├── _config/          # Agent configurations, manifests / 에이전트 설정
├── _memory/          # Persistent context for agents / 에이전트 문맥 저장
├── core/             # Core BMAD modules (skills, tasks) / 핵심 모듈
└── bmm/              # Business Method Module / 비즈니스 방법 모듈
    ├── agents/       # 9 agent personas / 9개 에이전트 페르소나
    ├── workflows/    # 4 workflow categories / 4개 워크플로우 카테고리
    └── teams/        # Team definitions / 팀 정의
```

---

## 8. bmad-docs/ — BMAD Documents / BMAD 문서

Artifacts produced by the BMAD workflow. These documents guided the entire development process.

BMAD 워크플로우에서 생성된 산출물. 이 문서들이 전체 개발 프로세스를 안내했습니다.

| Document / 문서 | Content / 내용 |
|---|---|
| `PRD.md` | Product Requirements Document — vision, personas, features, non-functional requirements / 제품 요구사항 문서 |
| `ARCHITECTURE.md` | System architecture — diagrams, component design, authentication, data flows / 시스템 아키텍처 |
| `STORIES.md` | User stories — feature breakdown into implementable stories / 사용자 스토리 |
| `TECH_STACK.md` | Technology standards — language, framework, Azure services, conventions / 기술 표준 |

---

## 9. scripts/ — Utility Scripts / 유틸리티 스크립트

| Script / 스크립트 | Purpose / 용도 |
|---|---|
| `create_agents.py` | Creates AI agents in Azure AI Foundry portal programmatically / Azure AI Foundry에서 프로그래밍 방식으로 에이전트 생성 |

---

## 10. tests/ — Test Suite / 테스트

| File / 파일 | Coverage / 범위 |
|---|---|
| `test_app.py` | API endpoint integration tests / API 엔드포인트 통합 테스트 |

---

## Navigation / 탐색

| Next / 다음 | Document / 문서 |
|---|---|
| How the AI works / AI 작동 방식 | → [docs/AI_ENGINE.md](AI_ENGINE.md) |
| Database & storage / 데이터베이스 & 저장소 | → [docs/DATABASE.md](DATABASE.md) |
| Network & deployment / 네트워크 & 배포 | → [docs/NETWORK.md](NETWORK.md) |
| BMAD methodology / BMAD 방법론 | → [docs/BMAD.md](BMAD.md) |
