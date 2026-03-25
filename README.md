# 🇰🇷 Korean Biz Coach — Business Korean Speaking Coach / 비즈니스 한국어 회화 코치

> A business Korean teaching platform powered by Azure AI Foundry + Speech, supporting **real-time voice conversations**, text chat, pronunciation scoring, vocabulary management, and learning progress tracking.
>
> Azure AI Foundry + Speech 기반의 비즈니스 한국어 교육 플랫폼. **실시간 음성 대화**, 텍스트 채팅, 발음 평가, 단어장 관리, 학습 진도 추적을 지원합니다.
>
> **Core Philosophy / 핵심 철학**: Teach natural Korean! Natural! Natural! Natural! — Real expressions from K-dramas, not textbook-style stiff 용어.
> 자연스러운 한국어를 가르칩니다! 자연스럽게! — 교과서식 딱딱한 표현이 아닌, 한국 드라마에서 나오는 실제 표현을 사용합니다.

**Live URL**: https://korean-biz-coach.azurewebsites.net

**Project Management / 프로젝트 관리**: BMAD-METHOD → see `bmad-docs/`

---

## 📸 Feature Overview / 기능 개요

| Feature / 기능 | Description / 설명 |
|------|------|
| 🎙️ **Real-time Voice Chat / 실시간 음성 대화** | WebSocket bidirectional voice communication with AI Korean coach "수진" / AI 한국어 코치 "수진"과 WebSocket 양방향 음성 통신 |
| 💬 **AI Text Chat / AI 텍스트 대화** | Detailed Korean teaching with GPT-5.2 + 9 MCP tools / GPT-5.2 기반 상세 한국어 교육, MCP 도구 9개 포함 |
| 🎤 **Voice Input / 음성 입력** | Azure Speech STT, supports Korean/Chinese/English / Azure Speech STT, 한/중/영 음성 인식 지원 |
| 🔊 **Natural Korean Voice / 자연스러운 한국어 음성** | Azure Speech TTS (SunHiNeural), SSML-tuned warm business voice / Azure Speech TTS (SunHiNeural), SSML 최적화된 따뜻한 비즈니스 목소리 |
| 📊 **Pronunciation Scoring / 발음 평가** | Azure Pronunciation Assessment, word-level accuracy scoring / Azure 발음 평가, 단어 단위 정확도 채점 |
| 🎬 **K-Drama Teaching Materials / 한국 드라마 교재** | Real dialogues from 《미생》《스타트업》《이태원클라쓰》《눈물의여왕》 / 실제 드라마 대사 활용 |
| 📝 **어미 Focus Teaching / 어미 중점 교육** | Natural sentence endings: -거든요, -잖아요, -더라고요, -네요 / 자연스러운 문장 어미 교육 |
| 📖 **Vocabulary Book / 단어장** | Add/delete/mark mastered, tag-based categorization / 추가/삭제/마스터 표시, 태그 기반 분류 |
| 📈 **Learning Progress / 학습 진도** | Streak tracking, study duration, 30-day bar chart / 연속 학습일, 학습 시간, 30일 차트 |

---

## 🏗️ Architecture / 아키텍처

> For detailed service connection diagrams and authentication methods, see [🔗 Azure Service Connection Details / Azure 서비스 연결 상세](#-azure-service-connection-details--azure-서비스-연결-상세) below.
>
> 상세한 서비스 연결 다이어그램 및 인증 방식은 아래 섹션을 참고하세요.

```
┌──────────────────────────────────────────────────────────────────┐
│              User (Browser / Mobile) / 사용자 (브라우저 / 모바일)  │
│                korean-biz-coach.azurewebsites.net                │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS + WebSocket
┌──────────────────────────▼───────────────────────────────────────┐
│              Azure App Service (Linux, Python 3.12, B1)          │
│              ┌──────────────────────────────────────────┐        │
│              │  FastAPI + Uvicorn (async)                │        │
│              │  ├── /static/*        → Web UI (HTML/JS)  │        │
│              │  ├── /api/auth/*      → JWT Auth / 인증   │        │
│              │  ├── /api/chat/*      → AI Agent Chat     │        │
│              │  ├── /ws/voice        → Real-time Voice WS│        │
│              │  ├── /api/vocab/*     → Vocab CRUD / 단어장│       │
│              │  ├── /api/progress/*  → Learning Progress │        │
│              │  └── /api/pronunciation → Scoring / 발음  │        │
│              └──────────────────────────────────────────┘        │
│              Managed Identity (Cognitive Services User)           │
│              VNet Integration → subnet-foithjjx                  │
└───────┬──────────────┬───────────────┬───────────────────────────┘
        │              │               │
   ┌────▼────┐   ┌─────▼──────┐  ┌────▼────┐  ┌────▼────────────────────────┐
   │  Azure   │   │  Azure      │  │   Azure  │  │   Azure AI Foundry      │
   │PostgreSQL│   │ Cosmos DB   │  │   Redis  │  │   (GPT-5.2 Agent)       │
   │14.21     │   │ NoSQL API   │  │  Basic   │  │   + Azure Speech        │
   │          │   │ Entra ID    │  │  SSL:6380│  │   (STT/TTS/Pronunciation│
   └──────────┘   └────────────┘  └─────────┘  │    Assessment / 발음평가)│
   Private EP    Entra ID     Private EP   └─────────────────────────┘
   VNet only     (no key)     VNet only     Identity-based auth
```

### Network Topology / 네트워크 토폴로지

```
VNet: vnet-zqopjmgp (Canada Central)
├── subnet-foithjjx       → App Service VNet Integration
├── subnet-ush4res52cpqu  → PostgreSQL Flexible Server (delegated / 위임)
└── cacheendpoint         → Redis Private Endpoint / Redis 프라이빗 엔드포인트
```

All data flows through VNet private network, no public exposure.
모든 데이터 통신은 VNet 사설 네트워크를 통하며, 공인 인터넷에 노출되지 않습니다.

---

## 🔐 Authentication Overview / 인증 방식 총괄

This project uses a **4-layer authentication system** covering user auth, Azure service-to-service auth, database, and cache.
이 프로젝트는 사용자 인증, Azure 서비스 간 인증, 데이터베이스, 캐시를 포괄하는 **4계층 인증 체계**를 사용합니다.

### 1. User Auth — JWT Bearer Token / 사용자 인증 — JWT Bearer 토큰

| Item / 항목 | Value / 값 |
|------|---|
| **Method / 방식** | `Authorization: Bearer <token>` |
| **Algorithm / 알고리즘** | HS256 |
| **Secret / 비밀키** | `JWT_SECRET=<your-jwt-secret>` |
| **Expiry / 만료** | 24 hours / 24시간 (1440 min) |
| **Issued by / 발급** | `POST /api/auth/login` or `/api/auth/register` |
| **Verified by / 검증** | `app/core/auth.py` → `get_current_user_id()` (FastAPI Depends) |
| **WebSocket** | First message: `{"type":"start","token":"..."}` / 첫 메시지에 포함 |

**Flow / 흐름**:
```
Register/Login → Server issues JWT → Client stores in localStorage → Sent in every request Header
회원가입/로그인 → 서버가 JWT 발급 → 클라이언트가 localStorage에 저장 → 매 요청 헤더에 포함
```

### 2. Azure Service Auth — Managed Identity (Keyless) / Azure 서비스 인증 — 관리 ID (키 없음)

| Item / 항목 | Value / 값 |
|------|---|
| **Method / 방식** | `DefaultAzureCredential()` → Managed Identity (prod) / AzureCliCredential (local) |
| **Scope** | `https://cognitiveservices.azure.com/.default` |
| **Principal ID** | `f18f4864-6999-45c2-95db-fc5c433d8eef` |
| **Role / 역할** | Cognitive Services User (AI Foundry + Speech) |
| **SDK** | `azure-identity` → `get_bearer_token_provider()` |

**Services covered / 적용 서비스**:
- ✅ Azure AI Foundry (GPT-5.2 Agent) — `AzureOpenAI(azure_ad_token_provider=...)`
- ✅ Azure Speech (STT/TTS/Pronunciation) — `Authorization: Bearer <token>`
- ✅ Azure Cosmos DB (NoSQL) — `DefaultAzureCredential` (Entra ID, no key / Entra ID, 키 없음)
- ❌ PostgreSQL — Username/password (Flexible Server doesn't support MI / MI 미지원)
- ❌ Redis — Access Key (Basic SKU, Redis 6.0 doesn't support Entra ID / Entra ID 미지원)

### 3. PostgreSQL Auth — Username/Password / PostgreSQL 인증 — 사용자명/비밀번호

| Item / 항목 | Value / 값 |
|------|---|
| **Username / 사용자명** | `<db-username>` |
| **Password / 비밀번호** | `<db-password>` (URL-encode special chars) |
| **Connection / 연결** | `postgresql+asyncpg://<user>:<password>@<server>.postgres.database.azure.com:5432/korean_biz?ssl=require` |
| **SSL** | Required / 필수 (`ssl=require` + `ssl.create_default_context()`) |
| **Access / 접근** | VNet private endpoint only, no public access / VNet 프라이빗 엔드포인트만, 공인 접근 없음 |

### 4. Redis Auth — Access Key / Redis 인증 — 액세스 키

| Item / 항목 | Value / 값 |
|------|---|
| **Access Key / 액세스 키** | `<redis-access-key>` |
| **Connection / 연결** | `rediss://:<redis-access-key-url-encoded>@aimee-cache.redis.cache.windows.net:6380/0` |
| **Protocol / 프로토콜** | `rediss://` (TLS/SSL) |
| **Port / 포트** | 6380 (SSL dedicated / SSL 전용) |
| **Fallback / 대체** | Connection failure → In-memory cache (automatic) / 연결 실패 → 메모리 캐시 (자동) |
| **Health check / 상태 확인** | `GET /api/chat/redis-check` → returns `auth_mode` + `status` |

---

## 🔗 Azure Service Connection Details / Azure 서비스 연결 상세

### Service Inventory / 서비스 목록

| # | Service / 서비스 | Resource Name / 리소스명 | Region / 지역 | SKU | Purpose / 용도 |
|---|------|---------|------|-----|------|
| 1 | **App Service** | `korean-biz-coach` | Canada Central | B1 Linux | Web app hosting / 웹 앱 호스팅 |
| 2 | **AI Foundry** | `gpt522222` | East US 2 | - | GPT-5.2 Agent |
| 3 | **Speech Service** | `gpt522222` | East US 2 | - | STT / TTS / Pronunciation Assessment / 발음 평가 |
| 4 | **PostgreSQL** | `aimeelan-server` | Canada Central | Flexible Server | Main database / 메인 데이터베이스 |
| 5 | **Redis** | `aimee-cache` | Canada Central | Basic C0 250MB | Session cache & rate limiting / 세션 캐시 & 속도 제한 |
| 6 | **Cosmos DB** | *(to be created)* | Canada Central | Serverless | Document data (conversations, drama, events) / 문서 데이터 |
| 7 | **VNet** | `vnet-zqopjmgp` | Canada Central | - | Private network / 사설 네트워크 |

### Connection Details for Each Link / 각 연결의 구체적 파라미터

#### ① App Service → AI Foundry (GPT-5.2)
```
Auth / 인증: Managed Identity → get_bearer_token_provider(cred, "cognitiveservices.azure.com/.default")
SDK:          openai.AzureOpenAI(azure_endpoint=..., azure_ad_token_provider=...)
API:          Responses API v2025-03-01-preview
Endpoint / 엔드포인트: https://gpt522222.services.ai.azure.com/api/projects/proj-default
Model / 모델: gpt-5.2
Agents / 에이전트: korean-biz-coach (text / 텍스트), sujin-voice (voice / 음성)
```

#### ② App Service → Azure Speech (STT)
```
Auth / 인증: Bearer token (Managed Identity)
Endpoint / 엔드포인트: https://gpt522222.cognitiveservices.azure.com/stt/speech/recognition/conversation/cognitiveservices/v1
Params / 파라미터: ?language=ko-KR (or zh-CN, en-US)
Format / 형식: audio/wav; codecs=audio/pcm; samplerate=16000
```

#### ③ App Service → Azure Speech (TTS)
```
Auth / 인증: Bearer token (Managed Identity)
Endpoint / 엔드포인트: https://gpt522222.cognitiveservices.azure.com/tts/cognitiveservices/v1
Format / 형식: SSML → ko-KR-SunHiNeural, friendly style, rate=0.95, pitch=+2%
Output / 출력: audio-16khz-128kbitrate-mono-mp3
```

#### ④ App Service → Azure Speech (Pronunciation Assessment / 발음 평가)
```
Auth / 인증: Bearer token (Managed Identity)
Endpoint / 엔드포인트: https://gpt522222.cognitiveservices.azure.com/stt/speech/recognition/conversation/cognitiveservices/v1
Header: Pronunciation-Assessment (Base64 JSON config)
Scoring / 채점: HundredMark, Word granularity / 100점 만점, 단어 단위
```

#### ⑤ App Service → PostgreSQL
```
Auth / 인증: Username/password (SSL required) / 사용자명/비밀번호 (SSL 필수)
Connection / 연결: postgresql+asyncpg://<user>:<password>@aimeelan-server.postgres.database.azure.com:5432/korean_biz?ssl=require
Pool / 풀: pool_size=10, max_overflow=20
ORM: SQLAlchemy async + asyncpg
```

#### ⑥ App Service → Redis
```
Auth / 인증: Access Key (SSL)
Connection / 연결: rediss://:<redis-access-key-url-encoded>@aimee-cache.redis.cache.windows.net:6380/0
Timeout / 타임아웃: socket_connect_timeout=5, socket_timeout=5
Fallback / 대체: Connection failure → In-memory dict (automatic) / 연결 실패 → 메모리 딕셔너리 (자동)
Keys / 키: thread:{uid}, ctx:{tid}, study:{uid}:today, streak:{uid}, rl:{uid}
```

---

## ⚙️ Complete Environment Variables / 전체 환경 변수 목록

### App Service Production (Configured) / App Service 프로덕션 (설정 완료)

| Variable / 변수 | Value / 값 | Description / 설명 |
|------|---|------|
| `AZURE_AI_ENDPOINT` | `https://gpt522222.services.ai.azure.com/api/projects/proj-default` | AI Foundry project endpoint / AI Foundry 프로젝트 엔드포인트 |
| `MODEL_DEPLOYMENT` | `gpt-5.2` | GPT model deployment / GPT 모델 배포명 |
| `TEXT_AGENT_NAME` | `korean-biz-coach` | Text mode agent / 텍스트 모드 에이전트 |
| `VOICE_AGENT_NAME` | `sujin-voice` | Voice mode agent / 음성 모드 에이전트 |
| `AZURE_SPEECH_REGION` | `eastus2` | Speech service region / 음성 서비스 지역 |
| `AZURE_SPEECH_RESOURCE_ENDPOINT` | `https://gpt522222.cognitiveservices.azure.com/` | Speech REST API endpoint / 음성 REST API 엔드포인트 |
| `AZURE_SPEECH_RESOURCE_ID` | `/subscriptions/<subscription-id>/resourceGroups/.../accounts/<resource>` | Speech resource ID / 음성 리소스 ID |
| `DATABASE_URL` | `postgresql+asyncpg://<user>:<password>@<server>:5432/korean_biz?ssl=require` | PostgreSQL connection string / PostgreSQL 연결 문자열 |
| `COSMOS_ENDPOINT` | *(to be configured after resource creation)* | Cosmos DB endpoint / Cosmos DB 엔드포인트 |
| `COSMOS_DATABASE` | `korean_biz` | Cosmos DB database name / Cosmos DB 데이터베이스명 |
| `REDIS_URL` | `rediss://:<access-key>@<host>:6380/0` | Redis connection string (SSL) / Redis 연결 문자열 (SSL) |
| `JWT_SECRET` | `<your-jwt-secret>` | JWT signing secret / JWT 서명 비밀키 |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Oryx build switch / Oryx 빌드 스위치 |
| `ENABLE_ORYX_BUILD` | `true` | Enable Oryx build / Oryx 빌드 활성화 |
| `WEBSITE_VNET_ROUTE_ALL` | `1` | Route all outbound through VNet / 모든 아웃바운드를 VNet으로 라우팅 |
| `WEBSITE_DNS_SERVER` | `168.63.129.16` | Azure DNS |
| `WEBSITES_CONTAINER_START_TIME_LIMIT` | `600` | Container startup timeout (sec) / 컨테이너 시작 타임아웃 (초) |
| `WEBSITE_HTTPLOGGING_RETENTION_DAYS` | `3` | HTTP log retention days / HTTP 로그 보존 일수 |
| `ORYX_DISABLE_COMPRESSING_OUTPUT` | `TRUE` | Disable Oryx output compression / Oryx 출력 압축 비활성화 |

### Local Development Override (.env.local) / 로컬 개발 오버라이드 (.env.local)

| Variable / 변수 | Value / 값 | Description / 설명 |
|------|---|------|
| `COSMOS_ENDPOINT` | *(empty for local mock)* | Cosmos DB endpoint (empty = mock) / Cosmos DB 엔드포인트 (비우면 mock) |
| `COSMOS_DATABASE` | `korean_biz` | Cosmos DB database name / Cosmos DB 데이터베이스명 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./korean_biz.db` | Local SQLite / 로컬 SQLite |
| `REDIS_URL` | `fake` | fakeredis in-memory / fakeredis 메모리 모드 |
| `DEBUG` | `true` | Debug mode / 디버그 모드 |

---

## 🔄 Data Flow / 데이터 흐름

### Text Chat Flow / 텍스트 대화 흐름
```
User input → POST /api/chat
사용자 입력 → POST /api/chat
  → JWT verification (get_current_user_id) / JWT 검증
  → Rate limiting (Redis: rl:{uid}, 60/min) / 속도 제한
  → Get/create conversation thread (Redis: thread:{uid}) / 대화 스레드 획득/생성
  → agent_service.chat()
    → AzureOpenAI Responses API (Managed Identity)
    → GPT-5.2 + 9 MCP Tools (vocab/grammar/K-drama/quiz...)
      (단어/문법/한국 드라마/퀴즈...)
    → previous_response_id maintains context / 컨텍스트 유지
  → Record study time (Redis: study:{uid}:today) / 학습 시간 기록
  → Return AI reply (JSON) / AI 응답 반환 (JSON)
```

### Real-time Voice Chat Flow (WebSocket) / 실시간 음성 대화 흐름 (WebSocket)
```
WebSocket /ws/voice
  → First message JWT auth {"type":"start","token":"..."}
    첫 메시지로 JWT 인증
  → Restore/create conversation thread / 대화 스레드 복원/생성

  Voice input / 음성 입력:
    → Client records audio (MediaRecorder WebM) / 클라이언트 녹음 (WebM)
    → Convert to WAV (OfflineAudioContext 16kHz) / WAV 변환
    → Send binary frames / 바이너리 프레임 전송
    → end_audio signal / 오디오 종료 신호
    → Azure Speech STT (Bearer Token, REST API)
    → Recognized text → agent_service.chat() (VOICE_INSTRUCTIONS)
      인식된 텍스트 → 에이전트 서비스
    → AI reply → Azure Speech TTS (SunHiNeural SSML)
      AI 응답 → TTS 변환
    → MP3 audio → Binary frame to client / MP3 → 클라이언트로 전송
    → JSON metadata (text, korean, audio_size)

  Text input / 텍스트 입력:
    → Skip STT, direct → Agent → TTS → Return
      STT 건너뛰기, 바로 → 에이전트 → TTS → 반환
```

### Pronunciation Assessment Flow / 발음 평가 흐름
```
POST /api/pronunciation (audio + reference_text)
  → JWT verification / JWT 검증
  → Azure Speech Pronunciation Assessment (REST API)
  → Returns word-level scoring (100-point scale)
    단어 단위 점수 반환 (100점 만점)
```

---

## 📁 Project Structure / 프로젝트 구조

```
korean-biz-agent/
├── app/                          # FastAPI backend / FastAPI 백엔드
│   ├── main.py                   # App entry (lifespan, CORS, routes, static)
│   │                             # 애플리케이션 진입점
│   ├── api/                      # API routes / API 라우트
│   │   ├── auth.py               # POST /register, /login, GET /profile
│   │   ├── chat.py               # POST /chat, /chat/voice, /chat/new-thread
│   │   ├── voice_ws.py           # WS /ws/voice — Real-time voice (WebSocket)
│   │   │                         # 실시간 음성 대화
│   │   ├── vocab.py              # GET/POST /vocab, PATCH/DELETE /vocab/{id}
│   │   ├── progress.py           # GET /progress, /lessons, /streaks
│   │   └── pronunciation.py      # POST /pronunciation
│   ├── core/                     # Infrastructure / 인프라
│   │   ├── config.py             # Pydantic Settings (.env + .env.local)
│   │   ├── database.py           # async SQLAlchemy (PostgreSQL/SQLite)
│   │   ├── cosmos.py             # Azure Cosmos DB (NoSQL, Entra ID auth)
│   │   │                         # COSMOS_ENDPOINT 空时自动用内存 Mock
│   │   ├── redis.py              # Redis (Azure/fakeredis)
│   │   └── auth.py               # JWT token create/verify / JWT 생성/검증
│   ├── models/
│   │   └── models.py             # 6 tables / 6개 테이블: User, Lesson, Progress,
│   │                             # Conversation, VocabBook, StudyStreak
│   ├── schemas/
│   │   └── schemas.py            # Pydantic request/response models
│   └── services/
│       ├── agent_service.py      # Azure AI Agent (GPT-5.2 + 9 MCP Tools)
│       ├── speech_service.py     # Azure Speech (STT/TTS/Pronunciation)
│       │                         # 음성 서비스 (음성인식/음성합성/발음평가)
│       ├── cosmos_service.py     # Cosmos DB CRUD (conversations, drama, events)
│       │                         # Cosmos DB 增删改查
│       └── cache_service.py      # Redis cache (session/rate-limit/streak)
│                                 # Redis 캐시 (세션/속도제한/연속학습)
├── mcp_server/
│   └── server.py                 # 9 MCP tools (vocab/grammar/K-drama/quiz...)
│                                 # 9개 MCP 도구 (단어/문법/한국드라마/퀴즈...)
├── data/
│   └── business_korean.json      # Teaching data (27KB) / 교육 데이터
├── static/                       # Web frontend / 웹 프론트엔드
│   ├── index.html                # Login/Register / 로그인/회원가입
│   ├── chat.html                 # Chat page (core) / 대화 페이지 (핵심)
│   ├── vocab.html                # Vocabulary book / 단어장
│   ├── progress.html             # Learning progress / 학습 진도
│   ├── style.css                 # Dark theme (purple design system)
│   └── app.js                    # Shared JS (Auth/API/Toast)
├── alembic/                      # Database migrations / 데이터베이스 마이그레이션
├── startup.sh                    # App Service startup script / 시작 스크립트
├── requirements.txt              # Python dependencies / Python 의존성
├── Dockerfile                    # Docker build / Docker 빌드
├── docker-compose.yml            # Local container orchestration / 로컬 컨테이너
├── .env                          # Production config / 프로덕션 설정
├── .env.local                    # Local dev override / 로컬 개발 오버라이드
└── README.md                     # ← You are here / 여기입니다
```

---

## 🔌 API Endpoints / API 엔드포인트

| Endpoint / 엔드포인트 | Method / 메서드 | Auth / 인증 | Description / 설명 |
|------|------|------|------|
| `/` | GET | ❌ | Redirect to Web UI / 웹 UI로 리다이렉트 |
| `/health` | GET | ❌ | Health check / 상태 확인 |
| `/ws/voice` | WS | ✅ | **Real-time voice chat (WebSocket) / 실시간 음성 대화** |
| `/api/auth/register` | POST | ❌ | Register → returns JWT / 회원가입 → JWT 반환 |
| `/api/auth/login` | POST | ❌ | Login → returns JWT / 로그인 → JWT 반환 |
| `/api/auth/profile` | GET | ✅ | Get user profile / 사용자 프로필 조회 |
| `/api/chat` | POST | ✅ | Text chat (Agent + MCP Tools) / 텍스트 대화 |
| `/api/chat/new-thread` | POST | ✅ | Create new conversation thread / 새 대화 스레드 생성 |
| `/api/chat/voice` | POST | ✅ | Voice chat REST (STT→Agent→TTS) / 음성 대화 REST |
| `/api/pronunciation` | POST | ✅ | Pronunciation scoring / 발음 평가 |
| `/api/vocab` | GET | ✅ | Get vocabulary list / 단어 목록 조회 |
| `/api/vocab` | POST | ✅ | Add vocabulary / 단어 추가 |
| `/api/vocab/{id}/master` | PATCH | ✅ | Toggle mastered status / 마스터 상태 전환 |
| `/api/vocab/{id}` | DELETE | ✅ | Delete vocabulary / 단어 삭제 |
| `/api/progress` | GET | ✅ | Learning progress overview / 학습 진도 개요 |
| `/api/lessons` | GET | ❌ | Lesson list / 강의 목록 |
| `/api/streaks` | GET | ✅ | Streak records / 연속 학습 기록 |

**Diagnostics / 진단 엔드포인트**:
| Endpoint / 엔드포인트 | Description / 설명 |
|------|------|
| `/api/chat/redis-check` | Redis connection status / Redis 연결 상태 |
| `/api/chat/speech-check` | Speech service status / 음성 서비스 상태 |
| `/api/chat/agent-check` | Agent service status / 에이전트 서비스 상태 |

Swagger docs / Swagger 문서: `https://korean-biz-coach.azurewebsites.net/docs`

---

## 🚀 Deployment / 배포

### Azure Resources (Created) / Azure 리소스 (생성 완료)

| Resource / 리소스 | Name / 이름 | Description / 설명 |
|------|------|------|
| Resource Group | `aimee-test-env` | Canada Central |
| App Service | `korean-biz-coach` | Python 3.12, B1 plan |
| PostgreSQL | `aimeelan-server` | Flexible Server 14.21, DB: `korean_biz` |
| Redis | `aimee-cache` | Basic 250MB, SSL port 6380 |
| AI Foundry | `gpt522222` | GPT-5.2, eastus2 |
| Speech | `gpt522222` | STT/TTS/Pronunciation, eastus2 |
| VNet | `vnet-zqopjmgp` | 3 subnets (App/DB/Cache) |

### Deploy to App Service / App Service에 배포

```bash
# 1. Login to Azure / Azure 로그인
az login

# 2. Deploy code / 코드 배포
cd korean-biz-agent
az webapp up -g aimee-test-env -n korean-biz-coach --runtime "PYTHON:3.12"

# 3. Check status / 상태 확인
az webapp show -g aimee-test-env -n korean-biz-coach --query state -o tsv
# → Running

# 4. View logs / 로그 확인
az webapp log tail -g aimee-test-env -n korean-biz-coach
```

---

## 💻 Local Development / 로컬 개발

```bash
# 1. Clone & virtual environment / 클론 & 가상 환경
git clone <repo>
cd korean-biz-agent
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 2. Local dev config (.env.local overrides .env — SQLite + fakeredis)
# 로컬 개발 설정 (.env.local이 .env를 오버라이드 — SQLite + fakeredis)
# .env.local already contains / .env.local에 이미 포함:
#   DATABASE_URL=sqlite+aiosqlite:///./korean_biz.db
#   REDIS_URL=fake

# 3. Azure CLI login (for AI Agent auth) / Azure CLI 로그인 (AI 에이전트 인증용)
az login

# 4. Start server / 서버 시작
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 5. Open browser / 브라우저 열기
# http://127.0.0.1:8000/
```

### Local vs Production / 로컬 vs 프로덕션

| | Local (.env.local) / 로컬 | Production (App Service) / 프로덕션 |
|--|---|---|
| Database / DB | SQLite (korean_biz.db) | Azure PostgreSQL (VNet) || Cosmos DB | In-memory mock (auto) / 메모리 Mock | Azure Cosmos DB (Entra ID) || Cache / 캐시 | fakeredis (in-memory / 메모리) | Azure Redis (SSL, VNet) |
| AI Auth / AI 인증 | AzureCliCredential | Managed Identity |
| JSON Column / JSON 컬럼 | JSON | JSONB |

---

## 🛠️ Tech Stack / 기술 스택

| Layer / 계층 | Technology / 기술 |
|---|---|
| **Backend / 백엔드** | Python 3.12, FastAPI, Uvicorn (async) |
| **AI Agent / AI 에이전트** | Azure AI Foundry, GPT-5.2, azure-ai-agents SDK |
| **Voice / 음성** | Azure Speech (STT/TTS/Pronunciation Assessment / 발음 평가) |
| **Database / 데이터베이스** | PostgreSQL 14 (relational, async via SQLAlchemy + asyncpg) + Cosmos DB (NoSQL documents, azure-cosmos) |
| **Cache / 캐시** | Azure Redis (SSL, aioredis) |
| **Auth / 인증** | JWT (PyJWT + bcrypt), Azure Managed Identity |
| **Frontend / 프론트엔드** | Vanilla HTML/CSS/JS (dark theme, responsive / 다크 테마, 반응형) |
| **MCP Tools / MCP 도구** | 9 tools (vocab/grammar/scenario/email/K-drama/endings/quiz) |
| **Deployment / 배포** | Azure App Service (Linux B1, VNet) |

---

## 🗄️ Database Architecture (Dual DB) / 데이터베이스 아키텍처 (듀얼 DB)

### PostgreSQL — Relational Data / 관계형 데이터 (5 Tables / 5개 테이블)

| Table / 테이블 | Key Fields / 주요 필드 | Description / 설명 |
|---|---|---|
| **users** | id, email (unique), hashed_password, korean_level, daily_goal_minutes | User accounts / 사용자 계정 |
| **lessons** | id, title, category (7 types), level, content (JSONB) | Course content / 강의 내용 |
| **learning_progress** | user_id, lesson_id, completed, score, quiz_results (JSONB) | Learning progress / 학습 진도 |
| **vocab_book** | user_id, word_ko, meaning_zh, mastered, review_count | Vocabulary book / 단어장 |
| **study_streak** | user_id, date, minutes_studied, lessons_completed | Study streak / 연속 학습 기록 |

### Cosmos DB — Document Data / 문서형 데이터 (3 Containers / 3개 컨테이너)

| Container / 컨테이너 | Partition Key / 파티션 키 | Description / 설명 |
|---|---|---|
| **conversations** | `/user_id` | Chat history — nested messages array, high write volume / 대화 기록 — 중첩 메시지 배열, 높은 쓰기 빈도 |
| **drama_content** | `/drama_id` | K-drama dialogues — rich nested scenes, cultural notes / 한국 드라마 대사 — 장면, 문화 노트 |
| **learning_events** | `/user_id` | Analytics events — append-only, 90-day TTL / 학습 이벤트 — 삽입전용, 90일 TTL |

**Data Flow / 데이터 흐름**:
```
User Request / 사용자 요청
    │
    ├── Auth, Profile, Vocab, Progress → PostgreSQL (SQLAlchemy)
    │    인증, 프로필, 단어장, 진도
    │
    ├── Chat / Voice conversation    → Cosmos DB (conversations)
    │    텍스트 / 음성 대화
    │
    ├── Drama content lookup         → Cosmos DB (drama_content)
    │    드라마 콘텐츠 조회
    │
    └── Learning analytics           → Cosmos DB (learning_events)
         학습 분석
```

> PostgreSQL uses JSONB, SQLite uses JSON. Cosmos DB uses native JSON documents. Column/document types auto-adapt.
> PostgreSQL은 JSONB, SQLite는 JSON, Cosmos DB는 네이티브 JSON 문서를 사용합니다. 타입이 자동 적응됩니다.

---

## 📱 Mobile / 모바일

The web frontend is responsive (`@media max-width: 768px`), accessible via mobile browser.
웹 프론트엔드는 반응형으로 구현되어 있으며 (`@media max-width: 768px`), 모바일 브라우저에서 바로 접근할 수 있습니다.

Future plans / 향후 계획:
- **PWA**: Add `manifest.json` + Service Worker → "Add to Home Screen" / "홈 화면에 추가"
- **React Native**: Native app → reuse same `/api/*` backend / 네이티브 앱 → 동일한 API 백엔드 재사용

---

## 📝 MCP Tools / MCP 도구 목록

The Agent can call 9 MCP tools to automatically query teaching data.
에이전트가 교육 데이터를 자동으로 조회할 수 있는 9개의 MCP 도구입니다.

| Tool / 도구 | Function / 기능 |
|------|------|
| `lookup_vocabulary` | Look up vocabulary by category / 카테고리별 어휘 조회 (meeting/email/phone/social) |
| `get_grammar_pattern` | Grammar pattern explanation / 문법 패턴 설명 (는데/거든요/잖아요...) |
| `generate_business_scenario` | Generate business scenario dialogues / 비즈니스 시나리오 대화 생성 |
| `get_email_template` | Business email templates / 비즈니스 이메일 템플릿 |
| `check_formality` | Check sentence formality level / 문장 경어 수준 확인 |
| `quiz_me` | Korean quiz / 한국어 퀴즈 |
| `get_drama_dialogue` | K-drama business dialogues / 한국 드라마 비즈니스 대화 (미생/스타트업...) |
| `get_sentence_endings` | Sentence ending usage / 어미 용법 (연결/종결/비격식) |
| `practice_conversation` | Conversation practice scenarios / 회화 연습 시나리오 |

---

## 📄 License / 라이선스

MIT
