# Product Requirements Document (PRD)
## Korean Business Coach — 실시간 음성 대화형 한국어 비즈니스 교육 플랫폼

### 1. 제품 개요 (Product Overview)

**제품명**: Korean Biz Coach (한국어 비즈니스 코치)

**비전**: 실시간 음성 + 텍스트 대화를 통해, 한국 드라마에서 나오는 **진짜 한국인이 쓰는 자연스러운 비즈니스 한국어**를 가르치는 AI 코칭 플랫폼.

**핵심 차별점**:
- 교과서 한국어가 아닌, **한국 드라마 기반의 지도적인(地道的) 비즈니스 표현**
- 실시간 음성 대화: WebSocket 기반 양방향 음성 통신
- 어미(語尾) 중심 교육: -거든요, -잖아요, -더라고요 등 실전 연결어미/종결어미
- Azure AD (Entra ID) 완전 무키 인증

---

### 2. 사용자 페르소나 (User Personas)

| Persona | Description |
|---------|------------|
| **학습자** | 중국/영어권 비즈니스 전문가, 한국 기업과 일하기 위해 자연스러운 비즈니스 한국어 필요 |
| **관리자** | 콘텐츠 관리, 학습 데이터 모니터링 |

---

### 3. 핵심 기능 요구사항 (Core Feature Requirements)

#### 3.1 실시간 음성 대화 (Real-time Voice Conversation)
- WebSocket 기반 양방향 음성 스트리밍
- Azure Speech SDK: STT (Speech-to-Text) + TTS (Text-to-Speech)
- 한국 여성 음성 (ko-KR-SunHiNeural) — 비즈니스 톤, 구어체
- Push-to-talk + 자동 음성 감지 모드
- 실시간 자막 표시

#### 3.2 텍스트 채팅 (Text Chat)
- AI 에이전트 기반 대화 (Azure AI Foundry)
- MCP 도구 통합 (어휘, 문법, 시나리오, 드라마 대사 등)
- 마크다운 렌더링

#### 3.3 한국 드라마 기반 콘텐츠 (K-Drama Based Content)
- 미생, 스타트업, 이태원클라쓰, 김과장, 비밀의숲 등
- 실제 대사 기반 패턴 교육
- 장면별 컨텍스트 (상사↔부하, 동료간, 거래처 등)

#### 3.4 어미/연결어미 중점 교육
- 종결어미: -거든요, -잖아요, -네요, -더라고요, -죠, -는데요
- 연결어미: -는데, -다가, -면서, -더니, -자마자
- 비격식 표현: 진짜요?, 대박, 아~ 그렇구나

#### 3.5 발음 평가 (Pronunciation Assessment)
- Azure Speech 발음 평가 API
- 단어별 정확도 점수
- 피드백 및 교정

#### 3.6 학습 진도 관리 (Progress Tracking)
- 일일 학습 목표, 연속 학습일
- 어휘장 (VocabBook)
- 퀴즈 성적 추적

---

### 4. 기술 아키텍처 (Technical Architecture)

```
┌─────────────────────────────────────────────────┐
│                    Frontend                      │
│         Vanilla JS + WebSocket Client            │
│         Voice UI + Text Chat + Dashboard         │
└─────────────┬──────────────┬────────────────────┘
              │ HTTPS/WSS    │
┌─────────────▼──────────────▼────────────────────┐
│              Azure App Service                   │
│              FastAPI + Uvicorn                    │
│                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ REST API │ │WebSocket │ │  Static Files    │ │
│  │ Endpoints│ │ Voice    │ │  (HTML/JS/CSS)   │ │
│  └────┬─────┘ └────┬─────┘ └──────────────────┘ │
│       │             │                            │
│  ┌────▼─────────────▼────────────────────────┐   │
│  │         Service Layer                      │   │
│  │  ┌─────────────┐ ┌────────────────────┐   │   │
│  │  │ AI Foundry  │ │  Speech Service    │   │   │
│  │  │ Agent SDK   │ │  STT/TTS/Assess    │   │   │
│  │  └──────┬──────┘ └────────┬───────────┘   │   │
│  │         │                 │               │   │
│  │  ┌──────▼──────┐ ┌───────▼────────────┐   │   │
│  │  │ MCP Tools   │ │ Cache Service      │   │   │
│  │  │ (9 tools)   │ │ (Redis)            │   │   │
│  │  └─────────────┘ └───────┬────────────┘   │   │
│  └───────────────────────────┼───────────────┘   │
└──────────────────────────────┼───────────────────┘
                               │
          ┌──────────┬─────────┼─────────┬──────────┐
          │          │         │         │          │
  ┌───────▼───────┐ ┌▼────────▼───┐ ┌───▼──────┐ ┌▼─────────────┐
  │  PostgreSQL   │ │ Cosmos DB   │ │  Redis   │ │ Azure AI      │
  │  (Relational) │ │ (Documents) │ │  Cache   │ │ Foundry+Speech│
  │  Private EP   │ │ NoSQL API   │ │Private EP│ │ Entra ID Auth │
  └───────────────┘ └─────────────┘ └──────────┘ └───────────────┘
```

### 5. 인증 전략 (Authentication Strategy)
- **모든 Azure 리소스**: Entra ID (Azure AD) — No API Keys
- **사용자 인증**: JWT (로컬 발급) → 추후 Entra ID B2C 확장 가능
- `DefaultAzureCredential` for all Azure SDK calls

### 6. 듀얼 데이터베이스 전략 (Dual Database Strategy)

| 데이터베이스 | 저장 데이터 | 이유 |
|-------------|-----------|------|
| **PostgreSQL** | users, lessons, learning_progress, vocab_book, study_streaks | 관계형 데이터, FK 제약조건, 집계 쿼리 |
| **Cosmos DB** | conversations, drama_content, learning_events | 문서형 데이터, 유연한 스키마, 대량 쓰기 |

- **Cosmos DB API**: NoSQL (SQL API)
- **인증**: `DefaultAzureCredential` (Entra ID, 키 없음)
- **파티션 키**: conversations → `/user_id`, drama_content → `/drama_id`, learning_events → `/user_id`
- **일관성 수준**: Session (기본값)
- **로컬 개발**: Cosmos DB Emulator 또는 인메모리 Mock

---

### 7. 비기능 요구사항 (Non-Functional Requirements)
- **응답 시간**: 음성 응답 < 3초 (STT + AI + TTS 전체)
- **동시 사용자**: 50+ (App Service B1)
- **가용성**: 99.5%
- **보안**: OWASP Top 10 준수, CORS 제한, Rate Limiting
