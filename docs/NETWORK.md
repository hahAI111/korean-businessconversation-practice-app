# 🌐 Network, Authentication & Deployment / 네트워크, 인증 & 배포

> API endpoints, WebSocket protocol, 4-layer authentication, Azure infrastructure, and deployment pipeline.
>
> API 엔드포인트, WebSocket 프로토콜, 4계층 인증, Azure 인프라, 배포 파이프라인.

---

## Table of Contents / 목차

1. [API Endpoint Reference / API 엔드포인트 참조](#1-api-endpoint-reference--api-엔드포인트-참조)
2. [WebSocket Protocol / WebSocket 프로토콜](#2-websocket-protocol--websocket-프로토콜)
3. [4-Layer Authentication / 4계층 인증](#3-4-layer-authentication--4계층-인증)
4. [Azure Infrastructure / Azure 인프라](#4-azure-infrastructure--azure-인프라)
5. [Network Topology / 네트워크 토폴로지](#5-network-topology--네트워크-토폴로지)
6. [Deployment Pipeline / 배포 파이프라인](#6-deployment-pipeline--배포-파이프라인)
7. [Environment Variables / 환경 변수](#7-environment-variables--환경-변수)

---

## 1. API Endpoint Reference / API 엔드포인트 참조

### Public Endpoints (No Auth) / 공개 엔드포인트 (인증 불필요)

| Endpoint / 엔드포인트 | Method | Description / 설명 |
|---|---|---|
| `/` | GET | Redirect to `/static/index.html` / 리다이렉트 |
| `/health` | GET | `{"status":"ok", "cosmos_db":"connected\|mock"}` |
| `/api/auth/register` | POST | Register new user → JWT / 회원가입 → JWT |
| `/api/auth/login` | POST | Login → JWT / 로그인 → JWT |
| `/api/lessons` | GET | List lessons (filter by category/level) / 강의 목록 |
| `/manifest.json` | GET | PWA manifest / PWA 매니페스트 |
| `/service-worker.js` | GET | PWA service worker / PWA 서비스 워커 |

### Authenticated Endpoints (JWT Required) / 인증 필요 엔드포인트

| Endpoint / 엔드포인트 | Method | Description / 설명 |
|---|---|---|
| `/api/auth/profile` | GET | User profile / 사용자 프로필 |
| `/api/chat` | POST | Text chat with AI agent / AI 에이전트와 텍스트 대화 |
| `/api/chat/tts` | POST | Text-to-speech conversion / 텍스트→음성 변환 |
| `/api/chat/new-thread` | POST | Create new conversation thread / 새 대화 스레드 생성 |
| `/api/chat/history` | GET | List conversation history / 대화 기록 목록 |
| `/api/chat/history/{thread_id}` | GET | Load specific conversation / 특정 대화 로드 |
| `/api/chat/history/{thread_id}` | DELETE | Delete conversation / 대화 삭제 |
| `/ws/voice` | WebSocket | Real-time voice chat / 실시간 음성 대화 |
| `/api/pronunciation` | POST | Pronunciation assessment / 발음 평가 |
| `/api/vocab` | GET | List vocabulary items / 단어 목록 |
| `/api/vocab` | POST | Add vocabulary / 단어 추가 |
| `/api/vocab/{id}/master` | PATCH | Toggle mastered status / 마스터 전환 |
| `/api/vocab/{id}` | PUT | Update vocabulary / 단어 수정 |
| `/api/vocab/{id}` | DELETE | Delete vocabulary / 단어 삭제 |
| `/api/progress` | GET | Learning dashboard / 학습 대시보드 |
| `/api/streaks` | GET | Study streak history / 연속 학습 기록 |
| `/api/progress/checkin` | POST | Daily check-in (打卡) / 일일 체크인 |

### Diagnostic Endpoints (No Auth) / 진단 엔드포인트

| Endpoint / 엔드포인트 | Checks / 확인 항목 |
|---|---|
| `/api/chat/redis-check` | Redis connection, auth_mode, ping status / Redis 연결 상태 |
| `/api/chat/speech-check` | Azure Speech token, Python version, ffmpeg / 음성 서비스 상태 |
| `/api/chat/agent-check` | Agent config validation / 에이전트 설정 검증 |

### Request/Response Examples / 요청/응답 예시

#### POST /api/chat — Text Chat / 텍스트 대화

```json
// Request / 요청
{
    "message": "How do I say 'nice to meet you' in natural Korean?",
    "thread_id": "thread_abc123"  // optional / 선택
}

// Response / 응답
{
    "reply": "In natural Korean, you'd say...\n\n**[Meeting Scene]**\n...",
    "thread_id": "thread_abc123",
    "tool_calls": ["lookup_vocabulary", "get_grammar_pattern"]
}
```

#### POST /api/chat/tts — Text to Speech / 텍스트→음성

```json
// Request / 요청
{ "text": "안녕하세요, 처음 뵙겠습니다." }

// Response / 응답
{ "audio_base64": "//uQxAAA..." }  // MP3 base64
```

#### POST /api/pronunciation — Pronunciation Score / 발음 점수

```json
// Request / 요청
{
    "audio_base64": "UklGR...",        // WAV base64
    "reference_text": "안녕하세요",
    "language": "ko-KR"               // optional / 선택
}

// Response / 응답
{
    "accuracy": 85.5,
    "fluency": 78.3,
    "completeness": 100.0,
    "pronunciation": 82.1,
    "words": [
        {"word": "안녕하세요", "accuracy": 85.5, "error_type": "None"}
    ]
}
```

---

## 2. WebSocket Protocol / WebSocket 프로토콜

### Connection Flow / 연결 흐름

```
Client                                    Server
클라이언트                                  서버
   │                                        │
   │──── WS Connect /ws/voice ─────────────►│
   │                                        │
   │──── {"type":"start",                   │
   │      "token":"jwt-token",             │
   │      "language":"auto"} ──────────────►│
   │                                        │ JWT verify → user_id
   │◄──── {"type":"ready",                 │ JWT 검증 → user_id
   │       "thread_id":"...",              │
   │       "message":"Connected"} ─────────│
   │                                        │
   │ ── CONVERSATION LOOP / 대화 반복 ──    │
   │                                        │
   │──── Binary (WAV audio chunk) ─────────►│
   │──── Binary (WAV audio chunk) ─────────►│
   │──── {"type":"end_audio"} ─────────────►│
   │                                        │ Collect → STT → Agent → TTS
   │◄──── {"type":"status",                │ 수집 → 음성인식 → 에이전트 → 음성합성
   │       "status":"processing"} ──────────│
   │                                        │
   │◄──── {"type":"transcript",            │
   │       "text":"인식된 텍스트"} ──────────│
   │                                        │
   │◄──── {"type":"reply",                 │
   │       "text":"AI 응답",               │
   │       "thread_id":"..."} ─────────────│
   │                                        │
   │◄──── Binary (MP3 audio) ──────────────│
   │                                        │
   │◄──── {"type":"status",                │
   │       "status":"ready"} ───────────────│
   │                                        │
   │ ── TEXT INPUT (alternative) / 텍스트 ──│
   │                                        │
   │──── {"type":"text",                   │
   │      "message":"텍스트 입력"} ─────────►│
   │                                        │ Skip STT → Agent → TTS
   │ ← (same response flow) ──             │ STT 건너뛰기
   │                                        │
   │ ── CONTROLS / 제어 ──                  │
   │                                        │
   │──── {"type":"new_thread"} ────────────►│ Create new thread
   │──── {"type":"set_language",           │ 새 스레드 생성
   │      "language":"ko-KR"} ─────────────►│ Change STT language
   │                                        │ STT 언어 변경
```

### Message Types / 메시지 유형

| Direction / 방향 | Type / 유형 | Purpose / 용도 |
|---|---|---|
| Client → Server | `start` | Initial auth with JWT token / JWT 토큰으로 초기 인증 |
| Client → Server | Binary | WAV audio frame / WAV 오디오 프레임 |
| Client → Server | `end_audio` | End of speech signal / 발화 종료 신호 |
| Client → Server | `text` | Text message (skip STT) / 텍스트 메시지 (STT 건너뛰기) |
| Client → Server | `new_thread` | Start new conversation / 새 대화 시작 |
| Client → Server | `set_language` | Change recognition language / 인식 언어 변경 |
| Server → Client | `ready` | Connection confirmed / 연결 확인 |
| Server → Client | `status` | Processing state / 처리 상태 |
| Server → Client | `transcript` | STT recognition result / 음성 인식 결과 |
| Server → Client | `reply` | AI response text / AI 응답 텍스트 |
| Server → Client | Binary | TTS MP3 audio / TTS MP3 오디오 |
| Server → Client | `error` | Error message / 오류 메시지 |

---

## 3. 4-Layer Authentication / 4계층 인증

The system uses 4 distinct authentication mechanisms, each solving a different trust problem.

시스템은 4개의 고유한 인증 메커니즘을 사용하며, 각각 다른 신뢰 문제를 해결합니다.

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: User → App / 사용자 → 앱                               │
│  ════════════════════════════════════════                        │
│  Method / 방식: JWT Bearer Token (HS256)                         │
│  Expiry / 만료: 24 hours                                         │
│  Transport / 전송:                                               │
│    HTTP: "Authorization: Bearer <token>"                         │
│    WebSocket: First msg {"type":"start","token":"<token>"}       │
│  Password / 비밀번호: bcrypt hash in PostgreSQL                  │
│                                                                  │
│  Flow / 흐름:                                                    │
│  Register/Login → JWT issued → localStorage → Every request      │
│  가입/로그인 → JWT 발급 → localStorage 저장 → 모든 요청에 포함    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: App → AI Foundry & Speech / 앱 → AI & 음성 서비스      │
│  ════════════════════════════════════════                        │
│  Method / 방식: Azure Managed Identity (keyless / 키 없음)       │
│  SDK: DefaultAzureCredential() → get_bearer_token_provider()    │
│  Scope: https://cognitiveservices.azure.com/.default             │
│  Role / 역할: Cognitive Services User                            │
│  Local / 로컬: AzureCliCredential (az login)                     │
│                                                                  │
│  Services covered / 적용 서비스:                                  │
│  ✅ Azure AI Foundry (GPT Agent)                                 │
│  ✅ Azure Speech (STT/TTS/Pronunciation)                         │
│  ✅ Azure Cosmos DB (Entra ID)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: App → PostgreSQL / 앱 → PostgreSQL                     │
│  ════════════════════════════════════════                        │
│  Method / 방식: Username + password + SSL                        │
│  Access / 접근: VNet private endpoint only (no public access)    │
│                 VNet 프라이빗 엔드포인트 전용 (공인 접근 없음)     │
│  Encoding: Special chars must be URL-encoded (! → %21)           │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: App → Redis / 앱 → Redis                               │
│  ════════════════════════════════════════                        │
│  Method / 방식: Access Key + SSL (TLS, port 6380)                │
│  Protocol / 프로토콜: rediss:// (note double 's')                │
│  Fallback / 대체: Connection failure → in-memory dict (auto)     │
│  Status / 상태: GET /api/chat/redis-check                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Azure Infrastructure / Azure 인프라

### Service Inventory / 서비스 목록

| # | Service / 서비스 | Resource Name / 리소스명 | Region / 지역 | SKU | Purpose / 용도 |
|---|---|---|---|---|---|
| 1 | **App Service** | `korean-biz-coach` | Canada Central | B1 Linux | Web hosting / 웹 호스팅 |
| 2 | **AI Foundry** | `gpt522222` | East US 2 | — | GPT Agent + MCP |
| 3 | **Speech Service** | `gpt522222` | East US 2 | — | STT/TTS/Pronunciation / 음성 |
| 4 | **PostgreSQL** | `aimeelan-server` | Canada Central | Flexible | Relational data / 관계형 데이터 |
| 5 | **Redis** | `aimee-cache` | Canada Central | Basic C0 | Cache / 캐시 |
| 6 | **Cosmos DB** | *(varies)* | Canada Central | Serverless | Document data / 문서 데이터 |
| 7 | **VNet** | `vnet-zqopjmgp` | Canada Central | — | Private network / 사설 네트워크 |

### Service Connections / 서비스 연결

```
┌─────────────────────────────────────────────────────────────────────┐
│                    App Service (korean-biz-coach)                     │
│                    Managed Identity + VNet Integration                │
│                    관리 ID + VNet 통합                                │
└────┬─────────────────┬──────────────────┬────────────────┬──────────┘
     │                 │                  │                │
     │ Managed ID      │ Managed ID       │ Username/Pass  │ Access Key
     │ 관리 ID         │ 관리 ID          │ 사용자/비번     │ 액세스 키
     │ (Token)         │ (Token)          │ + SSL          │ + SSL
     │                 │                  │                │
┌────▼────┐  ┌────────▼─────────┐  ┌─────▼──────┐  ┌─────▼──────┐
│ AI      │  │ Azure Speech     │  │PostgreSQL  │  │   Redis    │
│ Foundry │  │ (same endpoint)  │  │            │  │            │
│         │  │                  │  │ VNet only  │  │ Private EP │
│ GPT     │  │ STT / TTS /     │  │ VNet 전용   │  │ 프라이빗   │
│ Agent   │  │ Pronunciation   │  │            │  │            │
│         │  │ 음성 서비스      │  │            │  │            │
└─────────┘  └──────────────────┘  └────────────┘  └────────────┘
  East US 2     East US 2          Canada Central   Canada Central

                                   ┌────────────┐
                                   │ Cosmos DB  │
                                   │            │
                                   │ Entra ID   │
                                   │ (no key)   │
                                   │ (키 없음)   │
                                   └────────────┘
                                   Canada Central
```

---

## 5. Network Topology / 네트워크 토폴로지

```
                    Internet / 인터넷
                        │
                 ┌──────▼──────┐
                 │ App Service │
                 │ Public IP   │
                 │ 공인 IP     │
                 └──────┬──────┘
                        │
           VNet: vnet-zqopjmgp (10.0.0.0/16)
                 Canada Central
                        │
       ┌────────────────┼────────────────┐
       │                │                │
┌──────▼──────┐ ┌──────▼──────┐ ┌───────▼───────┐
│ subnet      │ │ subnet      │ │ cacheendpoint │
│ foithjjx    │ │ ush4res52...│ │               │
│             │ │             │ │               │
│ App Service │ │ PostgreSQL  │ │ Redis         │
│ Integration │ │ Delegation  │ │ Private EP    │
│ (outbound)  │ │ (dedicated) │ │ 프라이빗 EP   │
│  아웃바운드  │ │  전용       │ │               │
└─────────────┘ └─────────────┘ └───────────────┘
```

**Security / 보안**:
- PostgreSQL: VNet-only, no public endpoint / VNet 전용, 공인 엔드포인트 없음
- Redis: Private endpoint, SSL enforced (port 6380) / 프라이빗 엔드포인트, SSL 강제
- App Service: All outbound routed through VNet (`WEBSITE_VNET_ROUTE_ALL=1`) / 모든 아웃바운드 VNet 라우팅
- DNS: Azure internal DNS (`168.63.129.16`) for private endpoint resolution / 프라이빗 엔드포인트 DNS
- AI Foundry + Speech: Public endpoint, but Managed Identity auth (keyless) / 공인 엔드포인트, 관리 ID 인증

---

## 6. Deployment Pipeline / 배포 파이프라인

### Build & Deploy Flow / 빌드 & 배포 흐름

```
Developer (Local) / 개발자 (로컬)
    │
    │  1. python make_zip.py → deploy.zip
    │     (excludes: .env, __pycache__, .git, venv, etc.)
    │     (.env, __pycache__, .git, venv 등 제외)
    │
    │  2. az webapp deployment source config-zip \
    │       --resource-group myappservices \
    │       --name korean-biz-coach \
    │       --src deploy.zip
    │
    │  ⚠️ MUST use config-zip, NOT "az webapp deploy --type zip"
    │     반드시 config-zip 사용, "az webapp deploy --type zip" 사용 금지
    │
    ▼
┌──────────────────────────────────────────┐
│  Kudu (SCM Site)                         │
│  korean-biz-coach.scm.azurewebsites.net  │
│                                          │
│  1. Receive zip / zip 수신               │
│  2. Oryx build / Oryx 빌드              │
│     ├─ Detect requirements.txt           │
│     │  requirements.txt 감지             │
│     ├─ pip install → antenv/             │
│     │  pip 설치 → antenv/ 가상환경       │
│     └─ Output to /home/site/wwwroot      │
│        /home/site/wwwroot에 출력         │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│  Container (Debian Linux)                │
│  컨테이너 (Debian Linux)                 │
│                                          │
│  startup.sh:                             │
│    ├─ Activate antenv virtual env        │
│    │  antenv 가상환경 활성화              │
│    └─ python -m uvicorn app.main:app     │
│       --host 0.0.0.0 --port 8000         │
│       --workers 2                        │
│                                          │
│  Startup time / 시작 시간: ~4 min        │
│  Timeout / 타임아웃: 600 sec             │
└──────────────────────────────────────────┘
```

### Why config-zip? / 왜 config-zip인가?

| Method / 방법 | Oryx Build | Result / 결과 |
|---|---|---|
| `az webapp deployment source config-zip` ✅ | ✅ Triggered | pip install works, antenv created / pip 설치 정상 |
| `az webapp deploy --type zip` ❌ | ❌ Not triggered | No antenv → "No module named uvicorn" → 503 / 503 오류 |

---

## 7. Environment Variables / 환경 변수

### Required Variables / 필수 변수

| Variable / 변수 | Example / 예시 | Description / 설명 |
|---|---|---|
| `AZURE_AI_ENDPOINT` | `https://xxx.services.ai.azure.com/...` | AI Foundry project endpoint / AI Foundry 프로젝트 엔드포인트 |
| `MODEL_DEPLOYMENT` | `gpt-5-nano` | GPT model deployment name / GPT 모델 배포명 |
| `TEXT_AGENT_NAME` | `korean-biz-coach` | Portal text agent name / 포털 텍스트 에이전트명 |
| `VOICE_AGENT_NAME` | `sujin-voice` | Portal voice agent name / 포털 음성 에이전트명 |
| `AZURE_SPEECH_REGION` | `eastus2` | Speech service region / 음성 서비스 지역 |
| `AZURE_SPEECH_RESOURCE_ENDPOINT` | `https://xxx.cognitiveservices.azure.com/` | Speech REST API base URL / 음성 REST API URL |
| `AZURE_SPEECH_RESOURCE_ID` | `/subscriptions/.../accounts/xxx` | Speech resource ID for token / 토큰용 음성 리소스 ID |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host/db` | PostgreSQL connection string / PostgreSQL 연결 문자열 |
| `REDIS_URL` | `rediss://:key@host:6380/0` | Redis connection string / Redis 연결 문자열 |
| `JWT_SECRET` | `<random-string>` | JWT signing secret / JWT 서명 시크릿 |

### Optional Variables / 선택 변수

| Variable / 변수 | Default / 기본값 | Description / 설명 |
|---|---|---|
| `COSMOS_ENDPOINT` | `""` (mock) | Cosmos DB endpoint (empty = in-memory mock) / Cosmos DB 엔드포인트 |
| `COSMOS_DATABASE` | `korean_biz` | Cosmos DB database name / Cosmos DB 데이터베이스명 |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm / JWT 서명 알고리즘 |
| `JWT_EXPIRE_MINUTES` | `1440` (24h) | Token expiry / 토큰 만료 시간 |
| `DEBUG` | `false` | Debug mode / 디버그 모드 |

### App Service Settings / App Service 설정

| Setting / 설정 | Value / 값 | Purpose / 용도 |
|---|---|---|
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Enable Oryx build / Oryx 빌드 활성화 |
| `ENABLE_ORYX_BUILD` | `true` | Enable Oryx Python build / Oryx Python 빌드 |
| `WEBSITE_VNET_ROUTE_ALL` | `1` | Route outbound through VNet / 아웃바운드 VNet 라우팅 |
| `WEBSITE_DNS_SERVER` | `168.63.129.16` | Azure DNS for private endpoints / 프라이빗 엔드포인트 DNS |
| `WEBSITES_CONTAINER_START_TIME_LIMIT` | `600` | Startup timeout (sec) / 시작 타임아웃 |

---

## Navigation / 탐색

| Next / 다음 | Document / 문서 |
|---|---|
| How the AI works / AI 작동 방식 | → [docs/AI_ENGINE.md](AI_ENGINE.md) |
| Database & storage / 데이터베이스 & 저장소 | → [docs/DATABASE.md](DATABASE.md) |
| All files explained / 모든 파일 설명 | → [docs/CODEBASE.md](CODEBASE.md) |
| BMAD methodology / BMAD 방법론 | → [docs/BMAD.md](BMAD.md) |
