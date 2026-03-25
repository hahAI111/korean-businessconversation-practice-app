# 🇰🇷 Korean Biz Coach / 한국어 비즈니스 코치

> **A real-time AI business Korean speaking coach powered by Azure AI Foundry + Azure Speech**
>
> **Azure AI Foundry + Azure Speech 기반 실시간 AI 비즈니스 한국어 회화 코치**

Practice natural business Korean through real-time voice conversations with AI coach "수진 (Sujin)" — not textbook Korean, but **real Korean as spoken in K-dramas and Korean offices**.

AI 코치 "수진"과 실시간 음성 대화를 통해 자연스러운 비즈니스 한국어를 연습하세요 — 교과서 한국어가 아닌, **한국 드라마와 실제 한국 사무실에서 쓰는 진짜 한국어**를 배웁니다.

**🔗 Live Demo / 라이브 데모**: [korean-biz-coach.azurewebsites.net](https://korean-biz-coach.azurewebsites.net)

---

## ✨ Key Features / 주요 기능

| Feature / 기능 | Description / 설명 |
|---|---|
| 🎙️ **Real-time Voice Chat / 실시간 음성 대화** | WebSocket-based bidirectional voice conversation with AI. Speak in Korean, Chinese, or English — 수진 replies in natural Korean + English translation / WebSocket 기반 양방향 음성 대화. 한국어, 중국어, 영어로 말하면 수진이 자연스러운 한국어 + 영어 번역으로 답변 |
| 💬 **AI Text Chat / AI 텍스트 대화** | GPT-powered comprehensive Korean teaching with 9 specialized MCP tools / GPT 기반 종합 한국어 교육, 9개 전문 MCP 도구 포함 |
| 🎤 **Multi-language Voice Input / 다국어 음성 입력** | Auto-detect Korean, Chinese, English speech input (parallel STT) / 한국어, 중국어, 영어 음성 입력 자동 감지 (병렬 STT) |
| 🔊 **Natural Korean Voice / 자연스러운 한국어 음성** | Azure TTS with SSML-tuned warm business voice (SunHiNeural) / SSML 최적화된 따뜻한 비즈니스 목소리 |
| 📊 **Pronunciation Scoring / 발음 평가** | Word-level pronunciation accuracy assessment (100-point scale) / 단어 단위 발음 정확도 평가 (100점 만점) |
| 🎬 **K-Drama Teaching / 한국 드라마 교재** | Real dialogues from 미생, 스타트업, 이태원클라쓰, 눈물의여왕 / 실제 드라마 대사 활용 |
| 📝 **어미 Focus / 어미 중점 교육** | Natural sentence endings: -거든요, -잖아요, -더라고요, -네요 instead of textbook -습니다 / -습니다 대신 자연스러운 문장 어미 교육 |
| 📖 **Vocabulary Book / 단어장** | Add, edit, delete, tag, and master vocabulary with spaced review / 단어 추가/편집/삭제/태그/마스터 표시, 반복 학습 |
| 📈 **Learning Progress / 학습 진도** | Daily streak tracking, study duration chart, check-in system (打卡) / 연속 학습일, 학습 시간 차트, 체크인 시스템 |
| 📱 **PWA Mobile Support / PWA 모바일 지원** | Install as mobile app, offline support, responsive design / 모바일 앱 설치, 오프라인 지원, 반응형 디자인 |

---

## 🏗️ Architecture Overview / 아키텍처 개요

```
┌───────────────────────────────────────────────────────────────┐
│                Browser / Mobile (PWA)                         │
│                브라우저 / 모바일 (PWA)                          │
│     chat.html │ vocab.html │ progress.html │ index.html       │
└───────┬──────────────┬───────────────┬───────────────────────┘
        │ HTTPS        │ WebSocket     │ HTTPS
┌───────▼──────────────▼───────────────▼───────────────────────┐
│            Azure App Service (FastAPI + Uvicorn)              │
│                                                               │
│   ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────────┐ │
│   │ Auth    │ │ Chat    │ │ Voice WS │ │ Vocab/Progress   │ │
│   │ API     │ │ API     │ │ Handler  │ │ API              │ │
│   └────┬────┘ └────┬────┘ └────┬─────┘ └────────┬─────────┘ │
│        └──────┬─────┴──────────┴────────────────┘            │
│               ▼                                               │
│   ┌──────────────────────────────────────────────────┐       │
│   │              Service Layer / 서비스 계층           │       │
│   │  AgentService │ SpeechService │ CacheService      │       │
│   └──────┬────────────────┬───────────────┬──────────┘       │
└──────────┼────────────────┼───────────────┼──────────────────┘
           │                │               │
   ┌───────▼────────┐ ┌────▼──────┐ ┌──────▼──────┐
   │ Azure AI       │ │ Azure     │ │ Azure       │
   │ Foundry (GPT)  │ │ Speech    │ │ Redis       │
   │ + 9 MCP Tools  │ │ STT/TTS   │ │ Cache       │
   └────────────────┘ └───────────┘ └─────────────┘
                                           │
        ┌──────────────────┐    ┌──────────▼──────────┐
        │ Azure PostgreSQL │    │ Azure Cosmos DB     │
        │ (Users, Vocab,   │    │ (Conversations,     │
        │  Streaks)        │    │  K-Drama, Events)   │
        └──────────────────┘    └─────────────────────┘
```

---

## 📚 Documentation Index / 문서 목차

This project includes detailed documentation for every component. Each document is bilingual (English + Korean / 영어 + 한국어).

이 프로젝트는 모든 컴포넌트에 대한 상세 문서를 포함합니다. 모든 문서는 영한 이중 언어입니다.

| Document / 문서 | Description / 설명 |
|---|---|
| 📂 [docs/CODEBASE.md](docs/CODEBASE.md) | **Complete file & folder map** — Every file explained, line counts, responsibilities / 전체 파일 & 폴더 맵 — 모든 파일 설명, 줄 수, 역할 |
| 🧠 [docs/AI_ENGINE.md](docs/AI_ENGINE.md) | **AI system deep-dive** — How GPT Agent works, MCP tools, voice pipeline, instruction design / AI 시스템 심층 분석 — GPT 에이전트 작동 방식, MCP 도구, 음성 파이프라인, 지시문 설계 |
| 🗄️ [docs/DATABASE.md](docs/DATABASE.md) | **Data architecture** — Dual DB strategy, all tables/columns, Redis cache keys, data flow / 데이터 아키텍처 — 듀얼 DB 전략, 모든 테이블/컬럼, Redis 캐시 키, 데이터 흐름 |
| 🌐 [docs/NETWORK.md](docs/NETWORK.md) | **Communication & deployment** — API endpoints, WebSocket protocol, auth system, Azure infrastructure / 통신 & 배포 — API 엔드포인트, WebSocket 프로토콜, 인증 시스템, Azure 인프라 |
| 🔧 [docs/BMAD.md](docs/BMAD.md) | **BMAD methodology** — How BMAD v6.2 was used to build this project, agents, workflows, artifacts / BMAD 방법론 — BMAD v6.2를 활용한 프로젝트 구축 방법, 에이전트, 워크플로우, 산출물 |
| 📋 [bmad-docs/PRD.md](bmad-docs/PRD.md) | Product Requirements Document / 제품 요구사항 문서 |
| 🏛️ [bmad-docs/ARCHITECTURE.md](bmad-docs/ARCHITECTURE.md) | BMAD Architect's architecture design / BMAD 아키텍트의 아키텍처 설계 |
| 📖 [bmad-docs/STORIES.md](bmad-docs/STORIES.md) | User stories breakdown / 사용자 스토리 분류 |
| ⚙️ [bmad-docs/TECH_STACK.md](bmad-docs/TECH_STACK.md) | Technology standards / 기술 표준 |

---

## 🛠️ Tech Stack / 기술 스택

| Layer / 계층 | Technology / 기술 | Purpose / 용도 |
|---|---|---|
| **Backend / 백엔드** | Python 3.12, FastAPI, Uvicorn | Async web framework with WebSocket support / 비동기 웹 프레임워크, WebSocket 지원 |
| **AI Agent / AI 에이전트** | Azure AI Foundry, GPT, Responses API | Intelligent Korean teaching agent / 지능형 한국어 교육 에이전트 |
| **MCP Tools / MCP 도구** | FastMCP, 9 specialized tools | Vocabulary, grammar, K-drama, quiz, email, etc. / 어휘, 문법, 드라마, 퀴즈, 이메일 등 |
| **Voice / 음성** | Azure Speech REST API | STT (auto-detect) + TTS (SunHiNeural SSML) + Pronunciation scoring / 음성인식 + 음성합성 + 발음평가 |
| **Relational DB / 관계형 DB** | Azure PostgreSQL 14 (async) | Users, vocabulary, learning progress / 사용자, 단어장, 학습 진도 |
| **Document DB / 문서 DB** | Azure Cosmos DB (NoSQL) | Conversations, K-drama content, learning events / 대화, 드라마 콘텐츠, 학습 이벤트 |
| **Cache / 캐시** | Azure Redis (SSL) | Session cache, rate limiting, streak tracking / 세션 캐시, 속도 제한, 연속 학습 추적 |
| **Auth / 인증** | JWT (HS256) + Azure Managed Identity | User auth + Azure service-to-service auth / 사용자 인증 + Azure 서비스 간 인증 |
| **Frontend / 프론트엔드** | Vanilla HTML/CSS/JS, PWA | Zero-dependency, dark theme, mobile-ready / 의존성 제로, 다크 테마, 모바일 지원 |
| **Deploy / 배포** | Azure App Service (B1 Linux), VNet | Private network, Managed Identity / 사설 네트워크, 관리 ID |
| **Methodology / 방법론** | BMAD v6.2 | 9-agent agile framework for structured development / 9개 에이전트 애자일 프레임워크 |

---

## 🚀 Quick Start / 빠른 시작

### Prerequisites / 사전 요구사항

- Python 3.12+
- Azure account with AI Foundry + Speech Service / AI Foundry + Speech 서비스가 있는 Azure 계정
- Azure CLI (`az login`) for local development / 로컬 개발용 Azure CLI

### Local Development / 로컬 개발

```bash
# 1. Clone / 클론
git clone https://github.com/hahAI111/korean-businessconversation-practice-app.git
cd korean-businessconversation-practice-app

# 2. Virtual environment / 가상 환경
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux

# 3. Install dependencies / 의존성 설치
pip install -r requirements.txt

# 4. Configure environment / 환경 설정
# Copy .env.example to .env and fill in your Azure credentials
# .env.example을 .env로 복사하고 Azure 인증 정보를 입력하세요
cp .env.example .env

# 5. Azure CLI login (for Managed Identity auth) / Azure CLI 로그인
az login

# 6. Start server / 서버 시작
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 7. Open browser / 브라우저 열기
# → http://127.0.0.1:8000
```

### Local vs Production / 로컬 vs 프로덕션

| | Local (.env.local) / 로컬 | Production (App Service) / 프로덕션 |
|---|---|---|
| Database / DB | SQLite (korean_biz.db) | Azure PostgreSQL (VNet) |
| Cosmos DB | In-memory mock (auto) / 메모리 Mock | Azure Cosmos DB (Entra ID) |
| Cache / 캐시 | fakeredis (in-memory) / 메모리 | Azure Redis (SSL, VNet) |
| AI Auth / AI 인증 | AzureCliCredential | Managed Identity |

---

## 📁 Project Structure / 프로젝트 구조

```
korean-biz-agent/
├── app/                    # FastAPI application / FastAPI 애플리케이션
│   ├── main.py             # App entry point / 앱 진입점
│   ├── core/               # Infrastructure / 인프라 (config, DB, Redis, auth)
│   ├── api/                # Route handlers / 라우트 핸들러
│   ├── models/             # SQLAlchemy ORM models / ORM 모델
│   ├── schemas/            # Pydantic schemas / Pydantic 스키마
│   └── services/           # Business logic / 비즈니스 로직
├── mcp_server/             # 9 MCP teaching tools / 9개 MCP 교육 도구
├── data/                   # Teaching content (JSON) / 교육 콘텐츠
├── static/                 # Frontend + PWA / 프론트엔드 + PWA
├── docs/                   # Detailed documentation / 상세 문서
├── bmad-docs/              # BMAD methodology docs / BMAD 방법론 문서
├── _bmad/                  # BMAD framework / BMAD 프레임워크
├── alembic/                # Database migrations / DB 마이그레이션
├── tests/                  # Test suite / 테스트
├── startup.sh              # Azure App Service startup / 시작 스크립트
├── Dockerfile              # Container build / 컨테이너 빌드
├── docker-compose.yml      # Local orchestration / 로컬 오케스트레이션
└── requirements.txt        # Python dependencies / Python 의존성
```

> 📂 For a complete file-by-file explanation, see [docs/CODEBASE.md](docs/CODEBASE.md)
>
> 📂 파일별 상세 설명은 [docs/CODEBASE.md](docs/CODEBASE.md) 참조

---

## 🎯 Teaching Philosophy / 교육 철학

This is NOT a textbook Korean app. Korean Biz Coach teaches **natural Korean as actually spoken in Korean workplaces and K-dramas**.

이것은 교과서 한국어 앱이 아닙니다. Korean Biz Coach는 **한국 직장과 한국 드라마에서 실제로 사용하는 자연스러운 한국어**를 가르칩니다.

### What makes it different / 무엇이 다른가

| Textbook Korean / 교과서 한국어 | Korean Biz Coach |
|---|---|
| 감사합니다 (Thank you / 감사합니다) | 아, 감사합니다~ 정말 도움이 됐거든요 |
| 괜찮습니다 (It's okay / 괜찮습니다) | 네, 괜찮아요~ 이런 건 자주 있잖아요 |
| 확인하겠습니다 (I'll check / 확인하겠습니다) | 네, 확인해 볼게요. 좀 이따 알려드릴게요~ |
| 죄송합니다 (Sorry / 죄송합니다) | 아, 죄송해요~ 제가 깜빡했네요 |

### Key sentence endings taught / 가르치는 핵심 어미

| Ending / 어미 | Usage / 용법 | Example / 예시 |
|---|---|---|
| -거든요 | Giving reason / 이유 제시 | 늦어서 죄송해요, 회의가 길어졌**거든요** |
| -잖아요 | Shared knowledge / 공유된 지식 | 이 프로젝트 중요하**잖아요** |
| -더라고요 | Personal observation / 경험 관찰 | 어제 써봤는데 괜찮**더라고요** |
| -네요 | Discovery/surprise / 발견/놀라움 | 벌써 끝났**네요**! |
| -죠 | Seeking agreement / 동의 구하기 | 내일까지 맞**죠**? |

---

## 📄 License / 라이선스

MIT License

---

## 👤 Author / 작성자

**Jing Wang** — [GitHub](https://github.com/hahAI111)
