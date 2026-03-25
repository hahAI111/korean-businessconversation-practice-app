# 🔧 BMAD Methodology / BMAD 방법론

> How BMAD (Build Measure Analyze Decide) v6.2 was used to plan, design, and build this project.
>
> BMAD (Build Measure Analyze Decide) v6.2를 사용하여 이 프로젝트를 어떻게 계획, 설계, 구축했는지.

---

## Table of Contents / 목차

1. [What is BMAD? / BMAD란?](#1-what-is-bmad--bmad란)
2. [BMAD vs Runtime Code / BMAD vs 런타임 코드](#2-bmad-vs-runtime-code--bmad-vs-런타임-코드)
3. [9 Agent Personas / 9개 에이전트 페르소나](#3-9-agent-personas--9개-에이전트-페르소나)
4. [Workflow Phases / 워크플로우 단계](#4-workflow-phases--워크플로우-단계)
5. [How We Used BMAD / BMAD 활용 방법](#5-how-we-used-bmad--bmad-활용-방법)
6. [Output Artifacts / 산출물](#6-output-artifacts--산출물)
7. [Framework Structure / 프레임워크 구조](#7-framework-structure--프레임워크-구조)

---

## 1. What is BMAD? / BMAD란?

**BMAD (Build Measure Analyze Decide)** is an AI-powered agile development methodology framework (v6.2) that uses **9 specialized AI agent personas** to guide a software project through structured phases — from initial analysis to code review.

**BMAD**는 **9개의 전문 AI 에이전트 페르소나**를 사용하여 초기 분석부터 코드 리뷰까지 구조화된 단계를 통해 소프트웨어 프로젝트를 안내하는 AI 기반 애자일 개발 방법론 프레임워크(v6.2)입니다.

### Key Concept / 핵심 개념

Instead of one developer doing everything, BMAD breaks the work into **specialized roles**, each with specific expertise and responsibilities — like a virtual development team.

한 명의 개발자가 모든 것을 하는 대신, BMAD는 작업을 **전문화된 역할**로 나누며, 각각 특정 전문성과 책임을 가집니다 — 가상의 개발 팀처럼.

```
Traditional / 전통적:                  BMAD:
┌──────────────────┐            ┌──────────────────────────────────────┐
│  One Developer   │            │  PM → Architect → Dev → QA          │
│  does everything │            │  PM:       PRD & requirements       │
│  한 개발자가      │            │  Architect: System design            │
│  모든 것을 함     │            │  Dev:      Implementation            │
│                  │            │  QA:       Code review               │
│  = unstructured  │            │  = structured, documented            │
│  = 비구조화       │            │  = 구조화, 문서화                     │
└──────────────────┘            └──────────────────────────────────────┘
```

---

## 2. BMAD vs Runtime Code / BMAD vs 런타임 코드

**Important distinction / 중요한 구분**: BMAD is a **development process** tool, NOT runtime code. Nothing in `_bmad/` runs when the app is deployed.

**중요한 구분**: BMAD는 **개발 프로세스** 도구이지, 런타임 코드가 아닙니다. `_bmad/` 안의 어떤 것도 앱이 배포될 때 실행되지 않습니다.

| Aspect / 측면 | BMAD Framework (`_bmad/`) | App Code (`app/`) |
|---|---|---|
| **When used / 사용 시점** | During development / 개발 중 | At runtime / 런타임 |
| **Purpose / 용도** | Plan, design, review / 계획, 설계, 리뷰 | Serve users / 사용자 서비스 |
| **Users / 사용자** | Developers + AI assistants / 개발자 + AI 어시스턴트 | End users / 최종 사용자 |
| **Executes / 실행** | In IDE (VS Code Copilot) / IDE에서 | On Azure App Service / Azure에서 |
| **Output / 출력** | Documents (PRD, Architecture) / 문서 | API responses / API 응답 |

### How BMAD connects to the codebase / BMAD와 코드베이스의 연결

```
_bmad/ (Development Process / 개발 프로세스)
  │
  │  PM Agent writes PRD
  │  PM 에이전트가 PRD 작성
  │        ↓
  │  Architect designs system
  │  아키텍트가 시스템 설계
  │        ↓
  │  Dev implements code
  │  개발자가 코드 구현
  │        ↓
  │  QA reviews code
  │  QA가 코드 리뷰
  │
  └──────► bmad-docs/          ← Output documents / 산출 문서
           ├── PRD.md
           ├── ARCHITECTURE.md
           ├── STORIES.md
           └── TECH_STACK.md
                    │
                    │  Guides implementation
                    │  구현 안내
                    ↓
           app/                 ← Actual code / 실제 코드
           ├── api/
           ├── services/
           ├── models/
           └── ...
```

---

## 3. 9 Agent Personas / 9개 에이전트 페르소나

Each BMAD agent is a specialized AI persona with defined expertise, responsibilities, and output formats.

각 BMAD 에이전트는 정의된 전문성, 책임, 출력 형식을 가진 전문 AI 페르소나입니다.

| # | Agent / 에이전트 | Role / 역할 | What they do / 하는 일 |
|---|---|---|---|
| 1 | **Analyst** / 분석가 | Business Analyst / 비즈니스 분석가 | Analyzes requirements, user needs, market context. Creates project context. / 요구사항, 사용자 요구, 시장 컨텍스트 분석 |
| 2 | **PM** | Product Manager / 제품 관리자 | Writes PRD (Product Requirements Document), defines features, personas, success criteria / PRD 작성, 기능, 페르소나, 성공 기준 정의 |
| 3 | **Architect** / 아키텍트 | System Architect / 시스템 아키텍트 | Designs system architecture, selects tech stack, defines component interactions / 시스템 아키텍처 설계, 기술 스택 선택 |
| 4 | **Dev** / 개발자 | Developer / 개발자 | Implements features following architecture and stories. Writes actual code / 아키텍처와 스토리에 따라 기능 구현. 실제 코드 작성 |
| 5 | **QA** | Quality Analyst / 품질 분석가 | Reviews code for bugs, security, performance. Creates test plans / 버그, 보안, 성능 코드 리뷰. 테스트 계획 생성 |
| 6 | **SM** | Scrum Master / 스크럼 마스터 | Manages sprint workflow, breaks stories into tasks, tracks progress / 스프린트 워크플로우 관리, 스토리를 태스크로 분류 |
| 7 | **UX Designer** / UX 디자이너 | UX/UI Designer | Designs user experience, wireframes, interaction patterns / 사용자 경험, 와이어프레임, 인터렉션 패턴 설계 |
| 8 | **Tech Writer** / 기술 작가 | Technical Writer / 기술 작가 | Creates documentation, API docs, user guides / 문서 작성, API 문서, 사용자 가이드 |
| 9 | **Quick-Flow Solo Dev** / 퀵플로우 솔로 개발자 | Full-Stack Solo Developer / 풀스택 솔로 개발자 | Streamlined workflow for solo developers — combines PM+Architect+Dev+QA into one accelerated flow / 솔로 개발자를 위한 간소화 워크플로우 |

### Agent Configuration Files / 에이전트 설정 파일

Each agent has two files:

각 에이전트에는 두 개의 파일이 있습니다:

```
_bmad/bmm/agents/
├── pm.md                         # Agent definition / 에이전트 정의
│   └── Personality, expertise, responsibilities, output format
│       성격, 전문성, 책임, 출력 형식
│
_bmad/_config/agents/
├── bmm-pm.customize.yaml         # Project customization / 프로젝트 맞춤 설정
│   └── Project-specific overrides, constraints, preferences
│       프로젝트별 오버라이드, 제약, 선호
```

---

## 4. Workflow Phases / 워크플로우 단계

BMAD organizes development into **4 workflow categories** with a structured flow:

BMAD는 개발을 구조화된 흐름을 가진 **4개의 워크플로우 카테고리**로 구성합니다:

```
Phase 0               Phase 1              Phase 2              Phase 3
분석                   계획                  설계                  구현
────────────────────────────────────────────────────────────────────────
                                                                
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│ Analysis │────►│ Planning │────►│ Solutioning  │────►│ Implement│
│ 분석      │     │ 계획      │     │ 설계/해결    │     │ 구현   │
│          │     │          │     │              │     │          │
│ Analyst  │     │ PM       │     │ Architect    │     │ Dev + QA │
│ 분석가    │     │          │     │ 아키텍트     │     │ 개발+QA │
│          │     │          │     │              │     │          │
│ Output:  │     │ Output:  │     │ Output:      │     │ Output:  │
│ project- │     │ PRD.md   │     │ ARCH.md      │     │ Code +   │
│ context  │     │          │     │ TECH_STACK   │     │ Tests    │
│          │     │ STORIES  │     │              │     │ 코드+테스트│
└──────────┘     └──────────┘     └──────────────┘     └──────────┘
```

### Phase 0: Analysis / 분석

**Agent / 에이전트**: Analyst / 분석가
**Task / 태스크**: Create `project-context.md`

Analyzes the project idea, identifies target users, defines scope, and creates the foundational context document that all other phases reference.

프로젝트 아이디어를 분석하고, 대상 사용자를 식별하고, 범위를 정의하고, 다른 모든 단계에서 참조하는 기반 컨텍스트 문서를 생성합니다.

### Phase 1: Planning / 계획

**Agent / 에이전트**: PM (Product Manager)
**Tasks / 태스크**: Create PRD, define user stories

The PM writes a comprehensive PRD covering vision, personas, features, acceptance criteria, and non-functional requirements. Then breaks features into implementable user stories.

PM이 비전, 페르소나, 기능, 인수 기준, 비기능 요구사항을 포함하는 종합 PRD를 작성합니다. 그런 다음 기능을 구현 가능한 사용자 스토리로 분류합니다.

### Phase 2: Solutioning / 설계

**Agent / 에이전트**: Architect / 아키텍트
**Tasks / 태스크**: System architecture, tech stack selection

The Architect designs the complete system — component diagrams, data flows, authentication strategy, API design, and technology selection with rationale.

아키텍트가 완전한 시스템을 설계합니다 — 컴포넌트 다이어그램, 데이터 흐름, 인증 전략, API 설계, 근거가 있는 기술 선택.

### Phase 3: Implementation / 구현

**Agent / 에이전트**: Dev (Developer) + QA
**Tasks / 태스크**: Code implementation + code review

Developer implements features following the architecture and stories. QA reviews the code for correctness, security, and performance.

개발자가 아키텍처와 스토리에 따라 기능을 구현합니다. QA가 정확성, 보안, 성능에 대해 코드를 리뷰합니다.

---

## 5. How We Used BMAD / BMAD 활용 방법

Here's the exact BMAD workflow we followed to build Korean Biz Coach:

Korean Biz Coach를 구축하기 위해 따른 정확한 BMAD 워크플로우입니다:

### Step 1: Analyst → project-context.md / 분석가 → 프로젝트 컨텍스트

```
Input / 입력:  "Build a real-time voice Korean teaching app with AI"
              "AI를 활용한 실시간 음성 한국어 교육 앱 구축"

Analyst work / 분석가 작업:
  - Identified target audience: Chinese/English speakers learning business Korean
    대상: 비즈니스 한국어를 배우는 중국어/영어 화자
  - Defined core value: Real-time voice conversation, not textbook exercises
    핵심 가치: 교과서 연습이 아닌 실시간 음성 대화
  - Scoped MVP: Voice chat + text chat + vocabulary + progress
    MVP 범위: 음성 대화 + 텍스트 대화 + 단어장 + 진도

Output / 출력: project-context.md
```

### Step 2: PM → PRD.md + STORIES.md / PM → PRD + 스토리

```
PM work / PM 작업:
  - Vision statement / 비전 선언
  - 3 user personas / 3개 사용자 페르소나
  - 15+ feature descriptions / 15개 이상 기능 설명
  - Acceptance criteria for each feature / 각 기능의 인수 기준
  - Non-functional: <3s response, 50+ concurrent users
    비기능: 3초 미만 응답, 50명 이상 동시 사용자
  - User stories breakdown / 사용자 스토리 분류

Output / 출력: bmad-docs/PRD.md, bmad-docs/STORIES.md
```

### Step 3: Architect → ARCHITECTURE.md + TECH_STACK.md / 아키텍트

```
Architect work / 아키텍트 작업:
  - Designed dual database strategy (PostgreSQL + Cosmos DB)
    듀얼 DB 전략 설계
  - Selected FastAPI for WebSocket + async support
    WebSocket + 비동기 지원을 위해 FastAPI 선택
  - Designed 4-layer authentication system
    4계층 인증 시스템 설계
  - Defined VNet topology for security
    보안을 위한 VNet 토폴로지 정의
  - Specified SSML configuration for natural voice
    자연스러운 음성을 위한 SSML 설정 지정

Output / 출력: bmad-docs/ARCHITECTURE.md, bmad-docs/TECH_STACK.md
```

### Step 4: Dev (Barry Quick-Flow) → Code / 개발자 → 코드

```
Dev work / 개발 작업:
  - Implemented all API endpoints / 모든 API 엔드포인트 구현
  - Built WebSocket voice pipeline / WebSocket 음성 파이프라인 구축
  - Created 9 MCP tools / 9개 MCP 도구 생성
  - Built frontend (4 pages + PWA) / 프론트엔드 구축 (4페이지 + PWA)
  - Integrated all Azure services / 모든 Azure 서비스 통합
  - Performance optimization (async, pooling, fire-and-forget)
    성능 최적화 (비동기, 풀링, fire-and-forget)

Output / 출력: app/, mcp_server/, static/, data/
```

### Step 5: QA → Code Review / QA → 코드 리뷰

```
QA work / QA 작업:
  - Security review (JWT validation, input sanitization)
    보안 리뷰 (JWT 검증, 입력 살균)
  - Performance review (connection pooling, async patterns)
    성능 리뷰 (연결 풀링, 비동기 패턴)
  - Error handling review (fallback strategies)
    오류 처리 리뷰 (대체 전략)
  - Test coverage assessment / 테스트 커버리지 평가

Output / 출력: Code improvements, test_app.py
              코드 개선, test_app.py
```

---

## 6. Output Artifacts / 산출물

The BMAD workflow produced these key documents — all in `bmad-docs/`:

BMAD 워크플로우가 생성한 핵심 문서들 — 모두 `bmad-docs/`에:

| Document / 문서 | Lines | Content Summary / 내용 요약 |
|---|---|---|
| **PRD.md** | 700+ | Complete product spec: vision, personas, features, acceptance criteria, non-functional requirements / 완전한 제품 사양 |
| **ARCHITECTURE.md** | 600+ | System design: diagrams, components, auth, data flows, deployment / 시스템 설계 |
| **STORIES.md** | 300+ | User stories: feature breakdown into implementable chunks / 사용자 스토리 |
| **TECH_STACK.md** | 150+ | Technology decisions with rationale / 기술 결정 및 근거 |

These documents serve as:
이 문서들의 역할:
- **Living specification** / 살아있는 사양서 — always updated as the project evolves / 프로젝트 발전에 따라 항상 업데이트
- **Onboarding guide** / 온보딩 가이드 — new developers can understand the entire system / 새 개발자가 전체 시스템 이해
- **Decision log** / 의사결정 기록 — why each technology and design choice was made / 각 기술 및 설계 선택의 이유

---

## 7. Framework Structure / 프레임워크 구조

### Directory Layout / 디렉토리 레이아웃

```
_bmad/                              # BMAD Framework root / BMAD 프레임워크 루트
│
├── _config/                        # Configuration / 설정
│   ├── manifest.yaml               # Framework manifest (version, modules)
│   │                               # 프레임워크 매니페스트 (버전, 모듈)
│   ├── agent-manifest.csv          # All available agents / 사용 가능한 모든 에이전트
│   ├── skill-manifest.csv          # All available skills / 사용 가능한 모든 스킬
│   ├── task-manifest.csv           # All available tasks / 사용 가능한 모든 태스크
│   ├── workflow-manifest.csv       # All available workflows / 사용 가능한 모든 워크플로우
│   ├── tool-manifest.csv           # All available tools / 사용 가능한 모든 도구
│   ├── files-manifest.csv          # File references / 파일 참조
│   ├── bmad-help.csv               # Help index / 도움말 인덱스
│   └── agents/                     # Agent customizations / 에이전트 맞춤 설정
│       ├── bmm-pm.customize.yaml
│       ├── bmm-architect.customize.yaml
│       ├── bmm-dev.customize.yaml
│       ├── bmm-qa.customize.yaml
│       ├── bmm-sm.customize.yaml
│       ├── bmm-analyst.customize.yaml
│       ├── bmm-ux-designer.customize.yaml
│       ├── bmm-tech-writer.customize.yaml
│       └── bmm-quick-flow-solo-dev.customize.yaml
│
├── _memory/                        # Persistent context / 영구 컨텍스트
│   ├── config.yaml                 # Memory configuration / 메모리 설정
│   └── tech-writer-sidecar/        # Tech writer context / 기술 작가 컨텍스트
│       └── documentation-standards.md
│
├── core/                           # Core BMAD modules / 핵심 BMAD 모듈
│   ├── config.yaml                 # Core module config / 핵심 모듈 설정
│   ├── module-help.csv             # Help index / 도움말 인덱스
│   ├── skills/                     # Shared skills / 공유 스킬
│   └── tasks/                      # Shared tasks / 공유 태스크
│
└── bmm/                            # Business Method Module / 비즈니스 방법 모듈
    ├── config.yaml                 # BMM config / BMM 설정
    │   └── project: korean-biz-agent
    │       level: intermediate
    │       planning_artifacts: bmad-docs/
    │
    ├── agents/                     # 9 agent persona definitions / 9개 에이전트 정의
    │   ├── analyst.md              # Business Analyst / 비즈니스 분석가
    │   ├── pm.md                   # Product Manager / 제품 관리자
    │   ├── architect.md            # System Architect / 시스템 아키텍트
    │   ├── dev.md                  # Developer / 개발자
    │   ├── qa.md                   # Quality Analyst / 품질 분석가
    │   ├── sm.md                   # Scrum Master / 스크럼 마스터
    │   ├── quick-flow-solo-dev.md  # Solo developer shortcut / 솔로 개발자 단축
    │   └── tech-writer/            # Tech Writer / 기술 작가
    │       └── tech-writer.md
    │
    ├── workflows/                  # Workflow definitions / 워크플로우 정의
    │   ├── 1-analysis/             # Phase 0: Analysis / 분석
    │   ├── 2-plan-workflows/       # Phase 1: Planning / 계획
    │   ├── 3-solutioning/          # Phase 2: Design / 설계
    │   └── 4-implementation/       # Phase 3: Build / 구축
    │
    ├── teams/                      # Team compositions / 팀 구성
    └── data/                       # Project-specific data / 프로젝트별 데이터
```

### Key Files Explained / 주요 파일 설명

| File / 파일 | Purpose / 용도 |
|---|---|
| `bmm/config.yaml` | Configures BMAD for this specific project (name, level, output folder) / 이 프로젝트를 위한 BMAD 설정 |
| `bmm/agents/*.md` | Each file defines an agent's personality, expertise, and responsibilities / 각 파일이 에이전트의 성격, 전문성, 책임을 정의 |
| `_config/agents/*.customize.yaml` | Project-specific overrides for each agent / 각 에이전트의 프로젝트별 오버라이드 |
| `bmm/workflows/` | Step-by-step workflow instructions for each phase / 각 단계의 단계별 워크플로우 지침 |
| `_memory/` | Persistent context that agents can reference across sessions / 세션 간 에이전트가 참조할 수 있는 영구 컨텍스트 |

---

## Navigation / 탐색

| Next / 다음 | Document / 문서 |
|---|---|
| Main overview / 메인 개요 | → [README.md](../README.md) |
| How the AI works / AI 작동 방식 | → [docs/AI_ENGINE.md](AI_ENGINE.md) |
| Database & storage / 데이터베이스 & 저장소 | → [docs/DATABASE.md](DATABASE.md) |
| Network & deployment / 네트워크 & 배포 | → [docs/NETWORK.md](NETWORK.md) |
| All files explained / 모든 파일 설명 | → [docs/CODEBASE.md](CODEBASE.md) |
