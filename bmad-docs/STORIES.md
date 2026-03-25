# User Stories & Task Backlog
## Korean Biz Coach — BMAD Sprint Board

---

## Epic 1: Real-time Voice Conversation (실시간 음성 대화)

### Story 1.1: WebSocket Voice Endpoint
**As a** learner,
**I want** to have a real-time voice conversation with the AI coach,
**So that** I can practice speaking Korean naturally like in a phone call.

**Acceptance Criteria:**
- [ ] WebSocket endpoint at `/ws/voice`
- [ ] Binary audio frames for voice data
- [ ] JSON text frames for metadata (transcript, status)
- [ ] Auto-reconnect on disconnect
- [ ] Push-to-talk and continuous mode

### Story 1.2: Korean Female Voice (수진)
**As a** learner,
**I want** the AI coach to sound like a professional Korean woman,
**So that** the conversation feels natural and business-appropriate.

**Acceptance Criteria:**
- [ ] TTS uses `ko-KR-SunHiNeural` voice
- [ ] Conversational tone (not robotic)
- [ ] Appropriate speech rate for learning
- [ ] SSML prosody tuning for natural delivery

### Story 1.3: Voice + Text Unified Chat
**As a** learner,
**I want** to switch between voice and text input seamlessly,
**So that** I can use whichever is more convenient.

**Acceptance Criteria:**
- [ ] Same thread/conversation for voice and text
- [ ] Voice messages show transcript in chat
- [ ] Text messages can trigger audio reply

---

## Epic 2: Authentic Korean Teaching (地道한국어 교육)

### Story 2.1: K-Drama Content System
**As a** learner,
**I want** to learn Korean from real drama dialogues,
**So that** I speak naturally like a Korean person, not like a textbook.

**Acceptance Criteria:**
- [ ] Drama dialogue database (미생, 스타트업, 이태원클라쓰 등)
- [ ] Scene context (who's speaking, relationship, situation)
- [ ] All expressions with romanization + Chinese translation
- [ ] Cultural notes

### Story 2.2: Sentence Ending Focus (어미 중심)
**As a** learner,
**I want** to master natural sentence endings,
**So that** I sound like a native Korean speaker instead of always using -습니다/-요.

**Acceptance Criteria:**
- [ ] Comprehensive endings database
- [ ] Connectors (연결어미): -는데, -거든요, -잖아요, -더라고요
- [ ] Finals (종결어미): -네요, -죠, -더라, -냐고
- [ ] Casual expressions: 진짜?, 대박, 그쵸?

### Story 2.3: Business Context Teaching
**As a** learner,
**I want** to learn different registers for different business contexts,
**So that** I use appropriate Korean in meetings, emails, and casual team chats.

**Acceptance Criteria:**
- [ ] Formality checker tool
- [ ] Scenarios: meeting, email, phone, negotiation, networking
- [ ] Role-play with different hierarchies

---

## Epic 3: Azure Infrastructure (Entra ID, No Keys)

### Story 3.1: Full Entra ID Authentication
**As a** developer,
**I want** all Azure services to use Entra ID authentication,
**So that** there are no API keys in the codebase.

**Acceptance Criteria:**
- [ ] AI Foundry: DefaultAzureCredential
- [ ] Speech: DefaultAzureCredential → Bearer token
- [ ] PostgreSQL: connection string (VNet private, password auth)
- [ ] Redis: connection string (VNet private, access key in URL)
- [ ] No hardcoded API keys anywhere

### Story 3.2: App Service Deployment
**As a** developer,
**I want** automated deployment to Azure App Service,
**So that** the app is always available.

**Acceptance Criteria:**
- [ ] Oryx build pipeline
- [ ] VNet integration for private endpoints
- [ ] Managed Identity enabled
- [ ] Custom domain support

---

## Epic 4: Learning Management

### Story 4.1: Progress Dashboard
### Story 4.2: Vocabulary Book
### Story 4.3: Pronunciation Assessment
### Story 4.4: Quiz System

---

## Epic 5: Cosmos DB Integration (듀얼 데이터베이스)

### Story 5.1: Cosmos DB Core Layer
**As a** developer,
**I want** a reusable async Cosmos DB client integrated into the app,
**So that** document-oriented data can be stored separately from relational data.

**Acceptance Criteria:**
- [ ] `app/core/cosmos.py` — async CosmosClient with `DefaultAzureCredential`
- [ ] Config: `COSMOS_ENDPOINT`, `COSMOS_DATABASE` in `config.py`
- [x] Lifespan: init containers on startup, close client on shutdown
- [x] Local dev: in-memory mock (dict-based, no Emulator required)
- [x] Health check: `/health` includes Cosmos DB status

### Story 5.2: Conversations → Cosmos DB Migration ✅
**As a** developer,
**I want** chat conversations stored in Cosmos DB instead of PostgreSQL,
**So that** flexible document structure handles nested messages efficiently.

**Acceptance Criteria:**
- [x] Container: `conversations`, partition key: `/user_id`
- [x] `cosmos_service.py`: create/read/update/list conversation documents
- [x] `chat.py` + `voice_ws.py` API routes use Cosmos instead of SQLAlchemy
- [ ] Remove `Conversation` model from PostgreSQL models
- [x] Conversation document schema: `{id, user_id, thread_id, title, messages[], created_at, updated_at}`

### Story 5.3: K-Drama Content in Cosmos DB
**As a** developer,
**I want** K-drama dialogue content stored in Cosmos DB,
**So that** rich nested drama data (scenes, characters, cultural notes) uses flexible document schema.

**Acceptance Criteria:**
- [ ] Container: `drama_content`, partition key: `/drama_id`
- [ ] Document schema: `{id, drama_id, drama_name, episode, scene, characters[], dialogues[], grammar_points[], cultural_notes[], level}`
- [ ] MCP tools query drama_content from Cosmos DB
- [ ] Seed script loads initial drama data

### Story 5.4: Learning Events Analytics
**As a** developer,
**I want** fine-grained learning events stored in Cosmos DB,
**So that** we can track detailed user behavior for analytics and AI personalization.

**Acceptance Criteria:**
- [x] Container: `learning_events`, partition key: `/user_id`
- [x] Event types: `chat_message`, `voice_session`, `vocab_lookup`, `quiz_attempt`, `pronunciation_score`
- [x] Append-only pattern (no updates, only inserts)
- [x] TTL: 90 days (auto-expire old events)
- [x] Document schema: `{id, user_id, event_type, payload{}, timestamp}`
- [x] `chat.py` logs `chat_message` events after each reply
- [x] `voice_ws.py` logs `voice_message` / `voice_text_input` events after pipeline

---

## Sprint Plan

### Sprint 1 (Done): Core Voice + Chat ✅
1. ✅ WebSocket voice endpoint (`voice_ws.py`)
2. ✅ Enhanced Speech service with SSML
3. ✅ AI Agent with voice-specific instructions
4. ✅ Frontend voice UI with real-time feedback
5. ✅ All Entra ID authentication

### Sprint 2 (Current): Cosmos DB Integration 🚀
1. [x] Story 5.1 — Cosmos DB core layer (`cosmos.py`, config, lifespan)
2. [x] Story 5.2 — Conversations → Cosmos DB migration
3. [ ] Story 5.3 — K-Drama content in Cosmos DB
4. [x] Story 5.4 — Learning events analytics
5. [ ] Update README + deployment docs

### Sprint 3: Content & Polish
1. Expand K-drama dialogue database
2. Enhanced pronunciation assessment
3. Progress dashboard improvements
4. Mobile-responsive voice UI
