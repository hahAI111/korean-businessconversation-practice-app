---
stepsCompleted: [prerequisites, epic-decomposition, story-writing, acceptance-criteria, sprint-planning, review]
inputDocuments: [PRD.md, ARCHITECTURE.md, TECH_STACK.md, codebase-scan]
workflowType: 'epics-and-stories'
bmadAgent: 'SM Bob'
bmadVersion: '6.2.2'
lastUpdated: '2026-03-27'
---

# User Stories & Task Backlog
## Korean Biz Coach — BMAD Sprint Board

> **BMAD Agent**: SM Bob (Scrum Master) | **Phase**: 1-Planning → 3-Implementation
> **Status**: Living Document — reflects actual implementation state

---

## Epic 1: Real-time Voice Conversation (실시간 음성 대화) ✅ COMPLETE

### Story 1.1: WebSocket Voice Endpoint ✅
**As a** learner,
**I want** to have a real-time voice conversation with the AI coach,
**So that** I can practice speaking Korean naturally like in a phone call.

**Acceptance Criteria:**
- [x] WebSocket endpoint at `/ws/voice`
- [x] Binary audio frames for voice data
- [x] JSON text frames for metadata (transcript, status, reply)
- [x] JWT token validation in start frame
- [x] Push-to-talk and text input alternative mode

### Story 1.2: Korean Female Voice (수진) ✅
**As a** learner,
**I want** the AI coach to sound like a professional Korean woman,
**So that** the conversation feels natural and business-appropriate.

**Acceptance Criteria:**
- [x] TTS uses `ko-KR-SunHiNeural` voice
- [x] SSML prosody tuning for natural delivery
- [x] Voice-specific instructions (VOICE_INSTRUCTIONS, short 200-token responses)
- [x] Portal agent fallback: `sujin-voice`

### Story 1.3: Voice + Text Unified Chat ✅
**As a** learner,
**I want** to switch between voice and text input seamlessly,
**So that** I can use whichever is more convenient.

**Acceptance Criteria:**
- [x] Same thread/conversation for voice and text
- [x] Voice messages show transcript in chat
- [x] Text messages via `{"type":"text"}` in WebSocket

### Story 1.4: Auto Language Detection ✅
**As a** learner,
**I want** automatic language detection for my speech,
**So that** I can speak in Korean, English, or Chinese.

**Acceptance Criteria:**
- [x] Parallel STT for ko-KR, en-US, zh-CN
- [x] Automatic selection of best transcript
- [x] Configurable language preference

---

## Epic 2: Authentic Korean Teaching (地道한국어 교육) ✅ COMPLETE

### Story 2.1: K-Drama Content System ✅
**As a** learner,
**I want** to learn Korean from real drama dialogues,
**So that** I speak naturally like a Korean person, not like a textbook.

**Acceptance Criteria:**
- [x] Drama dialogue data in `business_korean.json`
- [x] MCP tool: `get_drama_dialogue()` with drama name + difficulty
- [x] Cultural notes and grammar points included
- [x] AI generation fallback when data unavailable

### Story 2.2: Sentence Ending Focus (어미 중심) ✅
**As a** learner,
**I want** to master natural sentence endings,
**So that** I sound like a native Korean speaker.

**Acceptance Criteria:**
- [x] MCP tool: `get_sentence_endings()` by category
- [x] Connectors (연결어미): -는데, -거든요, -잖아요, -더라고요
- [x] Finals (종결어미): -네요, -죠, -더라, -냐고
- [x] Casual expressions: 진짜?, 대박, 그쵸?

### Story 2.3: Business Context Teaching ✅
**As a** learner,
**I want** to learn different registers for different business contexts,
**So that** I use appropriate Korean in meetings, emails, and casual team chats.

**Acceptance Criteria:**
- [x] MCP tool: `check_formality()` for formality detection
- [x] MCP tool: `generate_business_scenario()` (meeting, negotiation, phone, etc.)
- [x] MCP tool: `get_email_template()` (business email templates)
- [x] MCP tool: `practice_conversation()` with role/formality settings

---

## Epic 3: Azure Infrastructure (Entra ID, No Keys) ✅ COMPLETE

### Story 3.1: Full Entra ID Authentication ✅
**As a** developer,
**I want** all Azure services to use Entra ID authentication,
**So that** there are no API keys in the codebase.

**Acceptance Criteria:**
- [x] AI Foundry: DefaultAzureCredential
- [x] Speech: DefaultAzureCredential → Bearer token
- [x] Cosmos DB: DefaultAzureCredential (Entra ID only)
- [x] PostgreSQL: connection string (VNet private, password auth)
- [x] Redis: connection string (VNet private, access key in URL)
- [x] No hardcoded API keys anywhere

### Story 3.2: App Service Deployment ✅
**As a** developer,
**I want** automated deployment to Azure App Service,
**So that** the app is always available.

**Acceptance Criteria:**
- [x] Oryx build pipeline (SCM_DO_BUILD_DURING_DEPLOYMENT)
- [x] VNet integration for private endpoints
- [x] Managed Identity enabled
- [x] startup.sh: zstd + ffmpeg installation
- [x] 2 Uvicorn workers

---

## Epic 4: Learning Management ✅ COMPLETE

### Story 4.1: Progress Dashboard ✅
**As a** learner,
**I want** to see my learning progress at a glance,
**So that** I stay motivated and track improvement.

**Acceptance Criteria:**
- [x] GET /api/progress — total lessons, completed, streak, study minutes, pronunciation avg
- [x] GET /api/lessons — list published lessons by category/level
- [x] GET /api/streaks — daily study streak history (30 days)
- [x] Frontend: `progress.html` with stats display

### Story 4.2: Vocabulary Book ✅
**As a** learner,
**I want** to save and review vocabulary words,
**So that** I build my business Korean vocabulary systematically.

**Acceptance Criteria:**
- [x] CRUD endpoints: GET, POST, PUT, DELETE /api/vocab
- [x] PATCH /api/vocab/{id}/master — toggle mastery
- [x] Tags (JSONB), review_count, next_review_at
- [x] Frontend: `vocab.html` with search/filter

### Story 4.3: Pronunciation Assessment ✅
**As a** learner,
**I want** to get scored on my Korean pronunciation,
**So that** I can improve my speaking accuracy.

**Acceptance Criteria:**
- [x] POST /api/pronunciation — score audio vs reference text
- [x] Scores: accuracy, fluency, completeness, pronunciation
- [x] Word-level breakdown

### Story 4.4: Daily Check-in ✅
**As a** learner,
**I want** to track my daily study habit,
**So that** I maintain consistency.

**Acceptance Criteria:**
- [x] POST /api/checkin — daily 打卡
- [x] Streak tracking (consecutive days)
- [x] Study session minutes recording (Redis)

---

## Epic 5: Cosmos DB Integration (듀얼 데이터베이스) ✅ COMPLETE

### Story 5.1: Cosmos DB Core Layer ✅
**Acceptance Criteria:**
- [x] `app/core/cosmos.py` — async CosmosClient with `DefaultAzureCredential`
- [x] Config: `COSMOS_ENDPOINT`, `COSMOS_DATABASE` in config.py
- [x] Lifespan: init containers on startup, close client on shutdown
- [x] Local dev: in-memory mock (dict-based, no Emulator required)
- [x] Health check: `/health` includes Cosmos DB status

### Story 5.2: Conversations → Cosmos DB ✅
**Acceptance Criteria:**
- [x] Container: `conversations`, partition key: `/user_id`
- [x] `cosmos_service.py`: create/read/update/list conversation documents
- [x] `chat.py` + `voice_ws.py` use Cosmos for conversation storage
- [x] Document schema: `{id, user_id, thread_id, title, messages[], timestamps}`

### Story 5.3: K-Drama Content in Cosmos DB 🔲 PLANNED
**Acceptance Criteria:**
- [ ] Container: `drama_content`, partition key: `/drama_id`
- [ ] Seed script loads initial drama data from business_korean.json
- [ ] MCP tools query drama_content from Cosmos DB
- [x] Container defined in cosmos.py

### Story 5.4: Learning Events Analytics ✅
**Acceptance Criteria:**
- [x] Container: `learning_events`, partition key: `/user_id`
- [x] Event types: chat_message, voice_session, vocab_lookup, quiz_attempt, pronunciation_score
- [x] Append-only pattern, TTL: 90 days
- [x] Event logging in chat.py and voice_ws.py

---

## Epic 6: User Authentication (사용자 인증) ✅ COMPLETE

### Story 6.1: Email Verification Registration ✅
**As a** user,
**I want** to register with email verification,
**So that** my account is secure and verified.

**Acceptance Criteria:**
- [x] POST /api/auth/send-code — 6-digit code via Azure Communication Services
- [x] Rate limiting: 60s between sends
- [x] Code stored in Redis (TTL 5min, memory fallback)
- [x] POST /api/auth/register — requires verification_code
- [x] bcrypt password hashing + HS256 JWT

### Story 6.2: Email/Password Login ✅
**Acceptance Criteria:**
- [x] POST /api/auth/login — bcrypt verify → JWT
- [x] JWT: HS256, 24h expiry, claims: sub(user_id), exp, iat

### Story 6.3: Microsoft Entra ID Login ✅
**As a** user,
**I want** to sign in with my Microsoft account,
**So that** I don't need a separate password.

**Acceptance Criteria:**
- [x] MSAL.js popup flow in frontend
- [x] POST /api/auth/microsoft — id_token validation
- [x] JWKS RS256 signature verification (cached 1h)
- [x] Auto-create user account on first login
- [x] Entra App: "Korean Biz Coach", single-tenant (fdpo.onmicrosoft.com)

### Story 6.4: User Profile ✅
**Acceptance Criteria:**
- [x] GET /api/auth/profile — JWT-protected, returns user info
- [x] Fields: id, email, nickname, korean_level, daily_goal_minutes, created_at

---

## Epic 7: Admin Dashboard (관리자 대시보드) ✅ COMPLETE

### Story 7.1: Admin Analytics API ✅
**As an** admin,
**I want** to see user activity metrics,
**So that** I can monitor platform health and growth.

**Acceptance Criteria:**
- [x] X-Admin-Key authentication (JWT_SECRET)
- [x] GET /api/admin/overview — KPIs (users, signups, DAU/WAU/MAU, content stats)
- [x] GET /api/admin/signups/trend — daily signup chart data
- [x] GET /api/admin/dau/trend — daily active users chart data
- [x] GET /api/admin/users — paginated user list with search/filter

### Story 7.2: Admin Dashboard UI ✅
**Acceptance Criteria:**
- [x] `admin_dashboard.html` — SPA with sidebar navigation
- [x] Login with admin key
- [x] KPI grid with core metrics
- [x] Charts (signups trend, DAU trend)
- [x] User management table with search, filter, pagination

---

## Epic 8: MCP Teaching Tools (교육 도구) ✅ COMPLETE

### Story 8.1: 9 FastMCP Tools ✅
**Acceptance Criteria:**
- [x] Mounted at `/mcp` for AI Foundry agent access
- [x] 9 tools: vocabulary, grammar, scenario, email, formality, quiz, drama, endings, conversation
- [x] Data source: `business_korean.json` with AI fallback
- [x] All tools return Korean + Chinese bilingual content

---

## Epic 9: PWA Support (앱 설치) ✅ COMPLETE

### Story 9.1: Progressive Web App ✅
**Acceptance Criteria:**
- [x] `service-worker.js` — offline caching strategy
- [x] `manifest.json` — app name, icons, theme
- [x] `offline.html` — offline fallback page
- [x] App icons (192x192, 512x512, apple-touch-icon)

---

## Epic 10: Production Resilience (프로덕션 안정성) ✅ COMPLETE

### Story 10.1: Redis Diagnostics & Fallback ✅
**Acceptance Criteria:**
- [x] `get_diagnostics()` — auth_mode, url_scheme, masked URL, last_error
- [x] `_mask_url()` — credential masking in logs
- [x] Memory fallback when Redis unavailable
- [x] `/api/chat/redis-check` returns diagnostic info

### Story 10.2: ffmpeg Audio Support ✅
**Acceptance Criteria:**
- [x] ffmpeg installed via `startup.sh` (apt-get)
- [x] Non-WAV → WAV conversion for STT
- [x] Pure Python resample fallback when ffmpeg unavailable
- [x] Warning logged (not error) for fallback path

---

## Sprint History

### Sprint 1 (Done): Core Voice + Chat ✅
1. ✅ WebSocket voice endpoint
2. ✅ Enhanced Speech service with SSML
3. ✅ AI Agent with voice-specific instructions
4. ✅ Frontend voice UI with real-time feedback
5. ✅ All Entra ID authentication

### Sprint 2 (Done): Cosmos DB Integration ✅
1. ✅ Story 5.1 — Cosmos DB core layer
2. ✅ Story 5.2 — Conversations → Cosmos DB
3. ✅ Story 5.4 — Learning events analytics
4. ⬜ Story 5.3 — K-Drama content in Cosmos DB (deferred)

### Sprint 3 (Done): Auth + Admin ✅
1. ✅ Email verification registration (ACS)
2. ✅ Microsoft Entra ID login (MSAL.js + JWKS)
3. ✅ Admin dashboard API + UI
4. ✅ Production resilience (Redis diagnostics, ffmpeg)

### Sprint 4 (Current): Content & Polish 🚀
1. ⬜ Expand K-drama dialogue database in Cosmos DB
2. ⬜ Enhanced pronunciation assessment feedback
3. ⬜ Progress dashboard improvements
4. ⬜ Mobile-responsive voice UI refinements
5. ⬜ CSV export for admin users
