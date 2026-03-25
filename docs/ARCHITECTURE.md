# 🏗️ Korean Biz Coach — System Architecture / 시스템 아키텍처

> Last updated / 최종 수정: 2026-03-20

---

## 1. System Overview / 시스템 개요

Korean Biz Coach is a business Korean teaching platform built on Azure Cloud. The core capability is **real-time voice conversation** — users have live Korean business dialogues with AI coach "수진", receiving instant feedback and pronunciation correction.

Korean Biz Coach는 Azure 클라우드 기반의 비즈니스 한국어 교육 플랫폼입니다. 핵심 기능은 **실시간 음성 대화** — 사용자가 AI 코치 "수진"과 한국어로 비즈니스 대화를 하며 즉각적인 피드백과 발음 교정을 받습니다.

### Tech Selection / 기술 선택

| Component / 구성요소 | Technology / 기술 | Why / 선택 이유 |
|------|------|-----------|
| Backend / 백엔드 | FastAPI + Uvicorn | Native async, WebSocket support, built-in OpenAPI docs / 비동기 네이티브, WebSocket 지원, OpenAPI 문서 내장 |
| AI Engine / AI 엔진 | Azure AI Foundry (GPT-5.2) | Responses API supports Agent + MCP Tools / Responses API가 Agent + MCP 도구 지원 |
| Voice / 음성 | Azure Speech REST API | STT/TTS/Pronunciation all-in-one, Identity-based auth / 음성인식/합성/발음평가 통합, 관리 ID 인증 |
| Database / DB | PostgreSQL 14 (async) | Flexible JSONB storage, async via asyncpg / JSONB 유연한 저장, asyncpg 비동기 |
| Cache / 캐시 | Azure Redis (SSL) | Session cache + rate limiting, auto-fallback to memory / 세션 캐시 + 속도 제한, 메모리 자동 대체 |
| Frontend / 프론트엔드 | Vanilla HTML/CSS/JS | Zero dependencies, dark theme, mobile-friendly / 의존성 제로, 다크 테마, 모바일 지원 |
| Deploy / 배포 | Azure App Service (Linux) | Managed Identity, VNet integration / 관리 ID, VNet 통합 |

---

## 2. Service Architecture Diagram / 서비스 아키텍처 다이어그램

```
                        ┌──────────────────────────────┐
                        │   User Browser / 사용자 브라우저│
                        │   (chat.html)                │
                        └────────────┬─────────────────┘
                                     │
                        HTTPS (443) + WebSocket (wss)
                                     │
┌────────────────────────────────────▼─────────────────────────────────────┐
│                  Azure App Service                                       │
│                  korean-biz-coach.azurewebsites.net                       │
│                  Linux | Python 3.12 | B1                                │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────┐           │
│   │                    FastAPI Application                    │           │
│   │                                                          │           │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │           │
│   │  │ auth.py  │ │ chat.py  │ │voice_ws  │ │ vocab.py   │ │           │
│   │  │ Login    │ │ Text Chat│ │ Voice WS │ │ Vocab CRUD │ │           │
│   │  │ 로그인   │ │ 텍스트   │ │ 음성 WS  │ │ 단어장     │ │           │
│   │  └────┬─────┘ └──┬──────┘ └──┬───────┘ └─────┬──────┘ │           │
│   │       │           │           │               │         │           │
│   │  ┌────▼───────────▼───────────▼───────────────▼──────┐ │           │
│   │  │           Service Layer / 서비스 계층              │ │           │
│   │  │                                                    │ │           │
│   │  │  agent_service ──── speech_service ──── cache_svc  │ │           │
│   │  └───────┬──────────────────┬──────────────────┬─────┘ │           │
│   └──────────┼──────────────────┼──────────────────┼───────┘           │
│              │                  │                  │                     │
│       ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐              │
│       │ Managed ID  │   │ Managed ID  │   │ Access Key  │              │
│       │ Bearer Token│   │ Bearer Token│   │ rediss://   │              │
│       └──────┬──────┘   └──────┬──────┘   └──────┬──────┘              │
│              │                 │                  │                      │
│   Managed Identity: f18f4864-6999-45c2-95db-fc5c433d8eef                │
│   관리 ID: f18f4864-6999-45c2-95db-fc5c433d8eef                         │
│   VNet Integration: subnet-foithjjx                                     │
└──────────────┼─────────────────┼──────────────────┼─────────────────────┘
               │                 │                  │
       ┌───────▼───────┐ ┌──────▼──────┐ ┌─────────▼─────────┐
       │ AI Foundry    │ │Azure Speech │ │   Azure Redis     │
       │ gpt522222     │ │ gpt522222   │ │   aimee-cache     │
       │ East US 2     │ │ East US 2   │ │   Canada Central  │
       │               │ │             │ │                   │
       │ GPT-5.2 Agent │ │ STT (ko/zh) │ │  thread:{uid}    │
       │ + 9 MCP Tools │ │ TTS (SSML)  │ │  ctx:{tid}       │
       │ Responses API │ │ Pronunciation│ │  study:{uid}     │
       │ v2025-03-01   │ │ 발음 평가   │ │  rl:{uid}        │
       └───────────────┘ └─────────────┘ └─────────┬─────────┘
                                                    │
       ┌────────────────────────────────────────────┼──────────┐
       │               VNet: vnet-zqopjmgp          │          │
       │                                            │          │
       │  ┌─────────────────────────────────┐       │          │
       │  │     Azure PostgreSQL            │       │          │
       │  │     aimeelan-server             │◄──────┘          │
       │  │     korean_biz DB               │  Private EP      │
       │  │     6 tables / 6개 테이블        │  프라이빗 EP    │
       │  │     Username/password auth (SSL)│                  │
       │  │     사용자명/비밀번호 인증       │                  │
       │  └─────────────────────────────────┘                  │
       └───────────────────────────────────────────────────────┘
```

---

## 3. Authentication Architecture / 인증 아키텍처

The system uses 4 authentication layers, each solving a different trust problem.
시스템은 4개의 인증 계층을 사용하며, 각각 다른 신뢰 문제를 해결합니다.

```
┌──────────────────────────────────────────────────────────────────┐
│ Layer 1: User → App Service / 사용자 → 앱 서비스                  │
│ Method / 방식: JWT Bearer Token (HS256)                           │
│ Secret / 비밀키: JWT_SECRET=<your-jwt-secret>  │
│ Expiry / 만료: 24h                                                │
│ Transport / 전송: HTTP Header "Authorization: Bearer <token>"     │
│                   WebSocket first msg {"type":"start","token":".."}│
│ Password / 비밀번호: bcrypt hash storage / bcrypt 해시 저장        │
├──────────────────────────────────────────────────────────────────┤
│ Layer 2: App Service → AI Foundry / Speech                        │
│          앱 서비스 → AI Foundry / 음성 서비스                      │
│ Method / 방식: Azure Managed Identity (keyless / 키 없음)          │
│ Principal: f18f4864-6999-45c2-95db-fc5c433d8eef                   │
│ Role / 역할: Cognitive Services User                               │
│ SDK: DefaultAzureCredential() → get_bearer_token_provider()       │
│ Scope: https://cognitiveservices.azure.com/.default                │
│ Local / 로컬: AzureCliCredential (az login)                        │
├──────────────────────────────────────────────────────────────────┤
│ Layer 3: App Service → PostgreSQL                                  │
│          앱 서비스 → PostgreSQL                                    │
│ Method / 방식: Username/password + SSL / 사용자명/비밀번호 + SSL   │
│ User / 사용자: <db-username>                                          │
│ Password / 비밀번호: <db-password> (URL-encode special chars)      │
│ Access / 접근: VNet private endpoint (no public) / VNet 전용        │
├──────────────────────────────────────────────────────────────────┤
│ Layer 4: App Service → Redis                                       │
│          앱 서비스 → Redis                                         │
│ Method / 방식: Access Key + SSL / 액세스 키 + SSL                  │
│ Key / 키: <redis-access-key>           │
│ Protocol / 프로토콜: rediss:// (TLS, port 6380)                    │
│ Fallback / 대체: Failure → in-memory dict (auto, no manual action) │
│                  실패 → 메모리 딕셔너리 (자동, 수동 조치 불필요)     │
│ Status / 상태: GET /api/chat/redis-check                           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Data Flows / 핵심 데이터 흐름

### 4.1 Text Chat / 텍스트 대화

```
┌──────┐    POST /api/chat     ┌──────────┐
│ User │ ───────────────────►  │ chat.py  │
│ 사용자│    {message: "..."}  └────┬─────┘
└──────┘                            │
                          ┌─────────▼───────────┐
                          │ 1. JWT → user_id    │
                          │ 2. Rate limit (Redis)│
                          │    속도 제한         │
                          │ 3. Get thread_id    │
                          │    스레드 ID 획득    │
                          └─────────┬───────────┘
                                    │
                          ┌─────────▼───────────┐
                          │  agent_service      │
                          │  AzureOpenAI.       │
                          │  responses.create() │
                          │                     │
                          │  model: gpt-5.2     │
                          │  + 9 MCP tools      │
                          │  + prev_response_id │
                          └─────────┬───────────┘
                                    │
                          ┌─────────▼───────────┐
                          │ 4. Record study time│
                          │    학습 시간 기록    │
                          │ 5. Return JSON reply│
                          │    JSON 응답 반환    │
                          └─────────────────────┘
```

### 4.2 Real-time Voice Chat (WebSocket) / 실시간 음성 대화 (WebSocket)

```
┌──────┐  WS /ws/voice   ┌────────────┐
│ User │ ◄─────────────► │ voice_ws   │
│ 사용자│ Bidirectional   └─────┬──────┘
└──────┘ 양방향 통신            │
                                │
   ┌────────────────────────────▼──────────────────────────────┐
   │              Message Flow / 메시지 흐름                    │
   │                                                           │
   │  1. {"type":"start","token":"JWT"} → Verify identity      │
   │     JWT 토큰으로 신원 확인                                  │
   │  2. Binary frames (WebM audio) → Collect                  │
   │     바이너리 프레임 (WebM 오디오) → 수집                    │
   │  3. {"type":"end_audio"} → Trigger recognition            │
   │     오디오 종료 → 인식 시작                                 │
   │                                                           │
   │  ┌─────────────────────────────────────────────────┐      │
   │  │ Voice Pipeline / 음성 파이프라인                  │      │
   │  │                                                  │      │
   │  │  WebM → WAV (16kHz) → Azure STT → Korean text   │      │
   │  │                                     한국어 텍스트 │      │
   │  │       ↓                                          │      │
   │  │  Text → GPT-5.2 Agent (VOICE_INSTRUCTIONS)      │      │
   │  │  텍스트 → GPT 에이전트                            │      │
   │  │       ↓                                          │      │
   │  │  AI reply → Azure TTS (SunHiNeural SSML) → MP3  │      │
   │  │  AI 응답 → TTS 변환 → MP3                        │      │
   │  │       ↓                                          │      │
   │  │  Binary frame (MP3) + JSON metadata → Client     │      │
   │  │  바이너리 (MP3) + JSON 메타데이터 → 클라이언트    │      │
   │  └─────────────────────────────────────────────────┘      │
   └───────────────────────────────────────────────────────────┘
```

### 4.3 Cache Strategy / 캐시 전략

```
Redis Key Design / Redis 키 설계:
  thread:{user_id}         → Current thread ID (string, TTL 24h)
                             현재 스레드 ID
  ctx:{thread_id}          → Conversation context cache (JSON, TTL 1h)
                             대화 컨텍스트 캐시
  study:{user_id}:today    → Today's study seconds (int, TTL 25h)
                             오늘 학습 시간(초)
  streak:{user_id}         → Consecutive study days (int, TTL 48h)
                             연속 학습일
  rl:{user_id}             → Rate limit counter (int, TTL 60s, max 60)
                             속도 제한 카운터

Fallback Strategy / 대체 전략:
  Redis OK     → _auth_mode = "access-key"
  fakeredis    → _auth_mode = "fake" (local dev / 로컬 개발)
  Redis failed → _auth_mode = "memory-fallback" (in-memory dict, not persistent)
  Redis 실패   → 메모리 딕셔너리, 비영속)
  Uninitialized→ _auth_mode = "not-connected" / 미초기화
```

---

## 5. API Endpoint Reference / API 엔드포인트 참조

### Public Endpoints (No Auth) / 공개 엔드포인트 (인증 불필요)

| Endpoint / 엔드포인트 | Method / 메서드 | Description / 설명 |
|------|------|------|
| `/` | GET | Redirect to `/static/index.html` / 리다이렉트 |
| `/health` | GET | `{"status":"ok","service":"Korean Biz Coach"}` |
| `/api/auth/register` | POST | Register (email + password → JWT) / 회원가입 |
| `/api/auth/login` | POST | Login (email + password → JWT) / 로그인 |
| `/api/lessons` | GET | Lesson list / 강의 목록 |

### Authenticated Endpoints (JWT Bearer) / 인증 필요 엔드포인트 (JWT Bearer)

| Endpoint / 엔드포인트 | Method / 메서드 | Description / 설명 |
|------|------|------|
| `/api/auth/profile` | GET | User profile / 사용자 프로필 |
| `/api/chat` | POST | Text chat (GPT-5.2 + MCP) / 텍스트 대화 |
| `/api/chat/new-thread` | POST | Create new thread / 새 스레드 생성 |
| `/api/chat/voice` | POST | Voice chat REST (STT→Agent→TTS) / 음성 대화 |
| `/ws/voice` | WS | Real-time voice WebSocket / 실시간 음성 |
| `/api/pronunciation` | POST | Pronunciation scoring / 발음 평가 |
| `/api/vocab` | GET/POST | Vocab list / Add vocab / 단어 목록 / 추가 |
| `/api/vocab/{id}/master` | PATCH | Toggle mastered / 마스터 전환 |
| `/api/vocab/{id}` | DELETE | Delete vocab / 단어 삭제 |
| `/api/progress` | GET | Learning progress / 학습 진도 |
| `/api/streaks` | GET | Streak records / 연속 학습 기록 |

### Diagnostic Endpoints (No Auth) / 진단 엔드포인트 (인증 불필요)

| Endpoint / 엔드포인트 | Description / 설명 | Checks / 확인 항목 |
|------|------|---------|
| `/api/chat/redis-check` | Redis connection / Redis 연결 | auth_mode, ping, status |
| `/api/chat/speech-check` | Speech service / 음성 서비스 | Python version, httpx, token, ffmpeg |
| `/api/chat/agent-check` | Agent service / 에이전트 서비스 | Config validation / 설정 검증 |

**Swagger Docs / Swagger 문서**: https://korean-biz-coach.azurewebsites.net/docs

---

## 6. Network Architecture / 네트워크 아키텍처

```
                        Internet / 인터넷
                           │
                    ┌──────▼──────┐
                    │  App Service │
                    │  Public IP   │
                    │  공인 IP     │
                    └──────┬──────┘
                           │
              VNet: vnet-zqopjmgp (10.0.0.0/16)
              Canada Central
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
   │ subnet      │ │ subnet      │ │ cacheendpoint│
   │ foithjjx    │ │ ush4res52.. │ │              │
   │             │ │             │ │              │
   │ App Service │ │ PostgreSQL  │ │ Redis        │
   │ Integration │ │ Delegation  │ │ Private EP   │
   │ (outbound)  │ │ (dedicated) │ │ 프라이빗 EP  │
   │  아웃바운드  │ │  전용       │ │              │
   └─────────────┘ └─────────────┘ └──────────────┘
```

**Security Notes / 보안 참고사항**:
- PostgreSQL: VNet-only access, no public endpoint / VNet 전용, 공인 엔드포인트 없음
- Redis: Private endpoint, SSL enforced (port 6380) / 프라이빗 엔드포인트, SSL 강제
- App Service: Outbound routed through VNet (`WEBSITE_VNET_ROUTE_ALL=1`) / 아웃바운드 VNet 라우팅
- DNS: Azure internal DNS (`168.63.129.16`) / Azure 내부 DNS
- AI Foundry / Speech: Public endpoint, Managed Identity auth / 공인 엔드포인트, 관리 ID 인증

---

## 7. Deployment Architecture / 배포 아키텍처

```
Developer (Local) / 개발자 (로컬)
    │
    │  az webapp up --runtime PYTHON:3.12
    │  or / 또는 az webapp deploy --type zip
    │
    ▼
┌──────────────────────────────────┐
│  Kudu (SCM Site)                 │
│  korean-biz-coach.scm.azure...   │
│                                  │
│  1. Receive zip / zip 수신       │
│  2. Oryx build / Oryx 빌드      │
│     - Detect requirements.txt    │
│       requirements.txt 감지      │
│     - pip install → antenv/      │
│     - Compress output (optional) │
│       출력 압축 (선택적)          │
│  3. Deploy to /home/site/wwwroot │
│     /home/site/wwwroot에 배포    │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Container (Debian Linux)        │
│  컨테이너 (Debian Linux)         │
│                                  │
│  startup.sh:                     │
│    1. Extract Oryx output        │
│       Oryx 출력 추출             │
│    2. Activate antenv venv       │
│       antenv 가상환경 활성화     │
│    3. python -m uvicorn          │
│       app.main:app               │
│       --host 0.0.0.0             │
│       --port 8000                │
│       --workers 1                │
│                                  │
│  Startup time / 시작 시간: ~4 min│
│  (cert update + pip + uvicorn)   │
│  Timeout / 타임아웃: 600 sec     │
└──────────────────────────────────┘
```

**Key App Settings / 주요 앱 설정**:

| Setting / 설정 | Value / 값 | Purpose / 용도 |
|------|---|------|
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Run Oryx build on code push / 코드 푸시 시 Oryx 빌드 실행 |
| `ENABLE_ORYX_BUILD` | `true` | Enable Oryx Python build / Oryx Python 빌드 활성화 |
| `WEBSITES_CONTAINER_START_TIME_LIMIT` | `600` | Container startup timeout 10 min / 컨테이너 시작 타임아웃 10분 |
| `WEBSITE_VNET_ROUTE_ALL` | `1` | Route all outbound through VNet / 모든 아웃바운드 VNet 라우팅 |
| `WEBSITE_DNS_SERVER` | `168.63.129.16` | Azure DNS for private endpoint resolution / 프라이빗 엔드포인트 DNS |

---

## 8. MCP Tools Architecture / MCP 도구 아키텍처

The Agent accesses 9 teaching tools via MCP (Model Context Protocol).
에이전트가 MCP (Model Context Protocol)를 통해 9개의 교육 도구에 접근합니다.

```
GPT-5.2 Agent / GPT-5.2 에이전트
    │
    │  function_call
    │
    ▼
┌──────────────────────────────────────────────────┐
│  mcp_server/server.py (FastMCP)                  │
│                                                  │
│  Data source / 데이터 소스:                       │
│    data/business_korean.json (27KB)              │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │ 1. lookup_vocabulary     Vocab lookup      │  │
│  │                          어휘 조회         │  │
│  │ 2. get_grammar_pattern   Grammar explain   │  │
│  │                          문법 설명         │  │
│  │ 3. generate_business_scenario  Scenario    │  │
│  │                                시나리오    │  │
│  │ 4. get_email_template    Business email    │  │
│  │                          비즈니스 이메일   │  │
│  │ 5. check_formality       Formality check   │  │
│  │                          경어 수준 확인    │  │
│  │ 6. quiz_me               Random quiz       │  │
│  │                          랜덤 퀴즈        │  │
│  │ 7. get_drama_dialogue    K-drama dialogue  │  │
│  │                          한국 드라마 대화  │  │
│  │ 8. get_sentence_endings  Ending usage      │  │
│  │                          어미 용법         │  │
│  │ 9. practice_conversation Conversation      │  │
│  │                          회화 연습         │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

**K-Drama Sources / 한국 드라마 교재**: 미생 (Misaeng), 스타트업 (Start-Up), 이태원클라쓰 (Itaewon Class), 눈물의여왕 (Queen of Tears)

---

## 9. Database Schema / 데이터베이스 스키마

```sql
-- 6 tables, async SQLAlchemy ORM
-- 6개 테이블, 비동기 SQLAlchemy ORM

users / 사용자
├── id (PK)
├── email (unique)
├── hashed_password (bcrypt)
├── korean_level              -- Korean proficiency / 한국어 수준
└── daily_goal_minutes        -- Daily study goal / 일일 학습 목표 (분)

lessons / 강의
├── id (PK)
├── title
├── category  -- meeting/email/phone/presentation/negotiation/social/general
│             -- 회의/이메일/전화/프레젠테이션/협상/소셜/일반
├── level     -- beginner/intermediate/advanced / 초급/중급/고급
└── content (JSONB)

learning_progress / 학습 진도
├── id (PK)
├── user_id (FK → users)
├── lesson_id (FK → lessons)
├── completed                 -- Completion status / 완료 여부
├── score                     -- Score / 점수
└── quiz_results (JSONB)

conversations / 대화
├── id (PK)
├── user_id (FK → users)
├── thread_id                 -- Responses API thread / 스레드 ID
└── messages (JSONB array)    -- Message history / 메시지 기록

vocab_book / 단어장
├── id (PK)
├── user_id (FK → users)
├── word_ko                   -- Korean word / 한국어 단어
├── meaning_zh                -- Chinese meaning / 중국어 뜻
├── mastered                  -- Mastered flag / 마스터 여부
└── review_count              -- Review count / 복습 횟수

study_streak / 연속 학습
├── id (PK)
├── user_id (FK → users)
├── date                      -- Study date / 학습 날짜
├── minutes_studied           -- Minutes studied / 학습 시간 (분)
└── lessons_completed         -- Lessons completed / 완료 강의 수
```

---

## 10. Local vs Production / 로컬 vs 프로덕션

| | Local (.env.local) / 로컬 | Production (App Service) / 프로덕션 |
|--|---|---|
| **Database / DB** | SQLite (korean_biz.db) | Azure PostgreSQL (VNet, SSL) |
| **Cache / 캐시** | fakeredis (in-memory / 메모리) | Azure Redis (SSL, port 6380) |
| **AI Auth / AI 인증** | AzureCliCredential (az login) | Managed Identity / 관리 ID |
| **JSON Column / JSON 컬럼** | JSON | JSONB |
| **Startup / 시작** | `uvicorn --reload` | `startup.sh` → uvicorn |
| **ffmpeg** | Optional install / 선택 설치 | Not available (Python fallback) / 불가 (Python 대체) |
| **CORS** | `allow_origins=["*"]` | Same / 동일 |
