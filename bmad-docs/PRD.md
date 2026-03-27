---
stepsCompleted: [discovery, personas, features, architecture, nfr, review]
inputDocuments: [project-context, codebase-scan]
workflowType: 'prd'
bmadAgent: 'PM John'
bmadVersion: '6.2.2'
lastUpdated: '2026-03-27'
---

# Product Requirements Document (PRD)
## Korean Business Coach — 실시간 음성 대화형 한국어 비즈니스 교육 플랫폼

> **BMAD Agent**: PM John (Product Manager) | **Phase**: 1-Planning
> **Status**: Living Document — reflects current production state

### 1. 제품 개요 (Product Overview)

**제품명**: Korean Biz Coach (한국어 비즈니스 코치)
**URL**: https://korean-biz-coach.azurewebsites.net

**비전**: 실시간 음성 + 텍스트 대화를 통해, 한국 드라마에서 나오는 **진짜 한국인이 쓰는 자연스러운 비즈니스 한국어**를 가르치는 AI 코칭 플랫폼.

**핵심 차별점**:
- 교과서 한국어가 아닌, **한국 드라마 기반의 지도적인(地道的) 비즈니스 표현**
- 실시간 음성 대화: WebSocket 기반 양방향 음성 통신
- 어미(語尾) 중심 교육: -거든요, -잖아요, -더라고요 등 실전 연결어미/종결어미
- Azure Entra ID 완전 무키 인증 + Microsoft OAuth 로그인
- PWA 지원: 오프라인 접근, 앱 설치 가능

---

### 2. 사용자 페르소나 (User Personas)

| Persona | Description | Auth Method |
|---------|------------|-------------|
| **학습자** | 중국/영어권 비즈니스 전문가, 한국 기업과 일하기 위해 자연스러운 비즈니스 한국어 필요 | Email+Code 또는 Microsoft Entra ID |
| **관리자** | 콘텐츠 관리, 학습 데이터 모니터링, 사용자 관리 | X-Admin-Key (JWT_SECRET) |

---

### 3. 핵심 기능 요구사항 (Core Feature Requirements)

#### 3.1 실시간 음성 대화 (Real-time Voice Conversation) ✅
- WebSocket 기반 양방향 음성 스트리밍 (`/ws/voice`)
- Azure Speech REST API: STT (Speech-to-Text) + TTS (Text-to-Speech)
- 한국 여성 음성 (ko-KR-SunHiNeural) — SSML 프로소디 튜닝
- Push-to-talk + 텍스트 입력 대안 모드
- 실시간 자막 표시 (transcript + reply)
- 자동 언어 감지 (ko-KR / en-US / zh-CN 병렬 STT)

#### 3.2 텍스트 채팅 (Text Chat) ✅
- Azure AI Foundry Agent (GPT-5-nano) + Responses API
- SSE 스트리밍 + 블로킹 모드 지원
- MCP 도구 통합 (9개 교육 도구)
- TTS 오디오 응답 (reply_audio_base64)
- 대화 히스토리 (Cosmos DB 저장)

#### 3.3 한국 드라마 기반 콘텐츠 (K-Drama Based Content) ✅
- 미생, 스타트업, 이태원클라쓰, 김과장, 비밀의숲 등
- 실제 대사 기반 패턴 교육
- 장면별 컨텍스트 (상사↔부하, 동료간, 거래처 등)
- MCP tool: `get_drama_dialogue()` — AI 생성 대체 지원

#### 3.4 어미/연결어미 중점 교육 ✅
- 종결어미: -거든요, -잖아요, -네요, -더라고요, -죠, -는데요
- 연결어미: -는데, -다가, -면서, -더니, -자마자
- 비격식 표현: 진짜요?, 대박, 아~ 그렇구나
- MCP tool: `get_sentence_endings()` — 카테고리별 검색

#### 3.5 발음 평가 (Pronunciation Assessment) ✅
- Azure Speech 발음 평가 API (`/api/pronunciation`)
- 단어별 정확도 점수 (accuracy, fluency, completeness, pronunciation)
- 피드백 및 교정

#### 3.6 학습 진도 관리 (Progress Tracking) ✅
- 일일 학습 목표 (daily_goal_minutes, 기본 15분)
- 연속 학습일 (study_streaks)
- 어휘장 (VocabBook — CRUD + 숙달 토글)
- 일일 체크인 (POST /api/checkin)
- 학습 이벤트 로깅 (Cosmos DB learning_events)

#### 3.7 사용자 인증 (User Authentication) ✅
- **이메일 인증 등록**: 6자리 코드 발송 (Azure Communication Services) → 검증 → 등록
- **이메일/비밀번호 로그인**: bcrypt + HS256 JWT
- **Microsoft Entra ID 로그인**: MSAL.js → RS256 id_token → JWKS 검증 → 자동 계정 생성
- 레이트 리밋: 60초당 1회 코드 발송
- Redis 코드 저장 (TTL 5분, 메모리 대체)

#### 3.8 관리자 대시보드 (Admin Dashboard) ✅
- 핵심 지표: 총 사용자, 일별/주별/월별 가입, DAU/WAU/MAU
- 가입 트렌드 차트 (일별)
- 일일 활성 사용자 트렌드 차트
- 사용자 목록: 검색, 필터, 페이지네이션
- X-Admin-Key 인증 (JWT_SECRET)

#### 3.9 MCP 교육 도구 (Teaching Tools) ✅
9개 FastMCP 도구 — AI Foundry Agent가 자동 호출:
1. `lookup_vocabulary` — 어휘 검색 (중/영/한/로마자)
2. `get_grammar_pattern` — 문법 패턴 설명
3. `generate_business_scenario` — 비즈니스 시나리오 생성
4. `get_email_template` — 비즈니스 이메일 템플릿
5. `check_formality` — 격식 수준 검사
6. `quiz_me` — 퀴즈 생성
7. `get_drama_dialogue` — 드라마 대사 학습
8. `get_sentence_endings` — 어미 패턴 검색
9. `practice_conversation` — 대화 연습 프레임워크

#### 3.10 PWA 지원 (Progressive Web App) ✅
- Service Worker (`service-worker.js`) — 오프라인 캐싱
- Web App Manifest (`manifest.json`) — 앱 설치
- 앱 아이콘 (192x192, 512x512, apple-touch-icon)

---

### 4. 기술 아키텍처 (Technical Architecture)

```
┌──────────────────────────────────────────────────────┐
│                     Frontend (PWA)                    │
│       Vanilla JS + WebSocket + MSAL.js + Service SW  │
│  6 Pages: index, chat, vocab, progress, admin, offline│
└──────────────┬──────────────┬────────────────────────┘
               │ HTTPS/WSS    │
┌──────────────▼──────────────▼────────────────────────┐
│              Azure App Service (B1 Linux)             │
│              FastAPI + Uvicorn (2 workers)            │
│                                                       │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────┐  │
│  │  REST API  │ │ WebSocket  │ │  Static Files    │  │
│  │ 25+ routes │ │ /ws/voice  │ │  (HTML/JS/CSS)   │  │
│  └─────┬──────┘ └─────┬──────┘ └──────────────────┘  │
│        │               │                              │
│  ┌─────▼───────────────▼─────────────────────────┐    │
│  │            Service Layer (5 services)          │    │
│  │  ┌──────────────┐ ┌────────────────────────┐  │    │
│  │  │ AgentService │ │  SpeechService         │  │    │
│  │  │ (AI Foundry) │ │  STT/TTS/Pronunciation │  │    │
│  │  └──────┬───────┘ └──────────┬─────────────┘  │    │
│  │  ┌──────▼──────┐ ┌──────────▼──────────────┐  │    │
│  │  │ MCP Server  │ │ CacheService (Redis)    │  │    │
│  │  │ (9 tools)   │ │ EmailService (ACS)      │  │    │
│  │  └─────────────┘ └──────────┬──────────────┘  │    │
│  │ ┌──────────────────────────────────────────┐   │    │
│  │ │ CosmosService (conversations, events)    │   │    │
│  │ └──────────────────────────┬───────────────┘   │    │
│  └─────────────────────────────┼─────────────────┘    │
└────────────────────────────────┼──────────────────────┘
                                 │
       ┌──────────┬──────────────┼──────────┬───────────┐
       │          │              │          │           │
┌──────▼───────┐ ┌▼─────────────▼┐ ┌───────▼────┐ ┌───▼──────────┐
│ PostgreSQL   │ │  Cosmos DB    │ │   Redis    │ │ Azure AI     │
│ (Users,      │ │ (Conversations│ │   Cache    │ │ Foundry +    │
│  Lessons,    │ │  Drama, Events│ │ (Sessions, │ │ Speech +     │
│  Progress,   │ │  NoSQL API)   │ │  Codes,    │ │ Communication│
│  VocabBook,  │ │               │ │  Rate-limit│ │ Services)    │
│  Streaks)    │ │               │ │            │ │              │
│ VNet Private │ │ Entra ID Auth │ │ VNet + SSL │ │ Managed ID   │
└──────────────┘ └───────────────┘ └────────────┘ └──────────────┘
```

### 5. 인증 전략 (Authentication Strategy)

#### 5.1 사용자 인증 (Dual Auth)
| Method | Flow | Token |
|--------|------|-------|
| **Email+Code** | send-code → register (with verification_code) → JWT | HS256 JWT (24h) |
| **Email+Password** | login → JWT | HS256 JWT (24h) |
| **Microsoft Entra ID** | MSAL.js → id_token → JWKS validate → auto-create user → JWT | RS256 → HS256 JWT |

#### 5.2 Azure 리소스 인증 (No API Keys)
- **AI Foundry**: `DefaultAzureCredential` → Bearer token
- **Speech**: `DefaultAzureCredential` → Bearer token (REST API)
- **Cosmos DB**: `DefaultAzureCredential` (Entra ID only)
- **PostgreSQL**: 비밀번호 (VNet private endpoint)
- **Redis**: Access key in URL (VNet private endpoint, SSL)
- **Email (ACS)**: HMAC-SHA256 서명 (connection string)

### 6. 듀얼 데이터베이스 전략 (Dual Database Strategy)

| 데이터베이스 | 저장 데이터 | 이유 |
|-------------|-----------|------|
| **PostgreSQL** | users, lessons, learning_progress, vocab_book, study_streaks, conversations (legacy) | 관계형 데이터, FK 제약조건, 집계 쿼리 |
| **Cosmos DB** | conversations, drama_content, learning_events | 문서형 데이터, 유연한 스키마, 대량 쓰기 |
| **Redis** | thread IDs, verification codes, rate limits, study sessions, streaks | 고속 캐시, TTL 기반 자동 만료 |

- **Cosmos DB API**: NoSQL (SQL API)
- **인증**: `DefaultAzureCredential` (Entra ID, 키 없음)
- **파티션 키**: conversations → `/user_id`, drama_content → `/drama_id`, learning_events → `/user_id`
- **일관성 수준**: Session (기본값)
- **로컬 개발**: 인메모리 Mock (dict 기반, Emulator 불필요)

---

### 7. 비기능 요구사항 (Non-Functional Requirements)
- **응답 시간**: 음성 응답 < 3초 (STT + AI + TTS 전체)
- **동시 사용자**: 50+ (App Service B1)
- **가용성**: 99.5%
- **보안**: OWASP Top 10 준수, CORS 제한, Rate Limiting, JWT 인증, Defender 활성화
- **PWA**: 오프라인 접근 가능, 모바일 설치 지원
- **로깅**: Python logger (print 사용 금지), 민감 정보 마스킹

---

### 8. API 엔드포인트 요약 (API Endpoint Summary)

| Category | Endpoints | Auth |
|----------|-----------|------|
| **Auth** | send-code, register, login, microsoft, profile | Public / JWT |
| **Chat** | chat, chat/stream, chat/tts, chat/new-thread, chat/history, chat/voice | JWT |
| **Voice** | /ws/voice (WebSocket) | JWT (token in start frame) |
| **Pronunciation** | /api/pronunciation | JWT |
| **Progress** | progress, lessons, streaks, checkin | JWT |
| **Vocab** | CRUD + master toggle | JWT |
| **Admin** | overview, signups/trend, dau/trend, users | X-Admin-Key |
| **Diagnostics** | health, agent-check, redis-check, cosmos-check, speech-check, stt-test, voice-test | Public |
| **MCP** | /mcp (9 tools via FastMCP) | Internal (Agent) |

**Total**: 25+ REST endpoints + 1 WebSocket + 9 MCP tools
