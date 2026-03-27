# 🔧 BMAD 방법론 / BMAD Methodology

> **최종 수정: 2026-03-27 | Last Updated: 2026-03-27**
>
> BMAD (Build Measure Analyze Decide) v6.2.2 프레임워크를 사용하여 이 프로젝트를 계획, 설계, 구축한 전체 과정을 기록합니다.
>
> This document records how the BMAD (Build Measure Analyze Decide) v6.2.2 framework was used to plan, design, and build this project.

---

## 목차 / Table of Contents

1. [BMAD란? / What is BMAD?](#1-bmad란--what-is-bmad)
2. [BMAD vs 런타임 코드 / BMAD vs Runtime Code](#2-bmad-vs-런타임-코드--bmad-vs-runtime-code)
3. [9개 에이전트 / 9 Agent Personas](#3-9개-에이전트--9-agent-personas)
4. [워크플로우 4단계 / 4 Workflow Phases](#4-워크플로우-4단계--4-workflow-phases)
5. [실제 적용: 7단계 전체 실행 / Real Execution: 7-Step Full Workflow](#5-실제-적용-7단계-전체-실행--real-execution-7-step-full-workflow)
6. [스프린트 이력 / Sprint History](#6-스프린트-이력--sprint-history)
7. [44개 스킬 참조 / 44 Skills Reference](#7-44개-스킬-참조--44-skills-reference)
8. [산출물 / Output Artifacts](#8-산출물--output-artifacts)
9. [프레임워크 구조 / Framework Structure](#9-프레임워크-구조--framework-structure)
10. [BMAD 호출 방법 / How to Invoke BMAD](#10-bmad-호출-방법--how-to-invoke-bmad)

---

## 1. BMAD란? / What is BMAD?

**BMAD**는 **9개의 전문 AI 에이전트 페르소나**와 **44개의 스킬**을 사용하여 소프트웨어 프로젝트를 구조적으로 진행하는 AI 기반 애자일 개발 프레임워크입니다 (v6.2.2).

**BMAD** is an AI-powered agile development framework (v6.2.2) that uses **9 specialized AI agent personas** and **44 skills** to guide software projects through structured phases.

### 핵심 개념 / Key Concept

한 명의 개발자가 모든 것을 하는 대신, BMAD는 작업을 **전문화된 역할**로 나눕니다 — 가상의 개발 팀처럼.

Instead of one developer doing everything, BMAD breaks work into **specialized roles** — like a virtual development team.

```
기존 방식:                          BMAD 방식:
┌──────────────────┐            ┌──────────────────────────────────────┐
│  개발자 1명이      │            │  분석가 → PM → 아키텍트 → 개발 → QA  │
│  모두 처리         │            │  Mary:    프로젝트 분석               │
│                  │            │  John:    PRD & 요구사항              │
│  = 비구조화        │            │  Winston: 시스템 설계                │
│                  │            │  Bob:     스프린트 계획               │
│  Traditional:    │            │  Barry:   코드 구현                  │
│  One dev does    │            │  Quinn:   코드 리뷰                  │
│  everything      │            │  Paige:   문서 작성                  │
│  = unstructured  │            │  = 구조화, 문서화 / structured        │
└──────────────────┘            └──────────────────────────────────────┘
```

---

## 2. BMAD vs 런타임 코드 / BMAD vs Runtime Code

**중요한 구분**: BMAD는 **개발 프로세스** 도구이지 런타임 코드가 아닙니다. `_bmad/` 안의 어떤 것도 앱 배포 시 실행되지 않습니다.

**Important**: BMAD is a **development process** tool, NOT runtime code. Nothing in `_bmad/` executes when the app is deployed.

| 측면 / Aspect | BMAD 프레임워크 (`_bmad/`) | 앱 코드 (`app/`) |
|---|---|---|
| **사용 시점 / When** | 개발 중 / During development | 런타임 / At runtime |
| **용도 / Purpose** | 계획, 설계, 리뷰 / Plan, design, review | 사용자 서비스 / Serve users |
| **사용자 / Users** | 개발자 + AI 어시스턴트 / Developers + AI | 최종 사용자 / End users |
| **실행 환경 / Runs in** | IDE (VS Code Copilot) | Azure App Service |
| **출력 / Output** | 문서 (PRD, Architecture) / Docs | API 응답 / API responses |

### BMAD → 코드베이스 연결 / BMAD → Codebase Connection

```
_bmad/ (개발 프로세스 / Development Process)
  │
  │  분석가 Mary    → project-context
  │  PM John       → PRD.md + STORIES.md
  │  아키텍트 Winston → ARCHITECTURE.md + TECH_STACK.md
  │  SM Bob        → Sprint 계획 + Story 상태
  │  개발자 Barry   → 코드 구현
  │  QA Quinn      → 코드 리뷰
  │  작가 Paige    → docs/ 문서
  │
  └──► bmad-docs/          ← 계획 산출물 / Planning artifacts
       ├── PRD.md           (BMAD 프론트매터 포함)
       ├── ARCHITECTURE.md  (BMAD frontmatter)
       ├── STORIES.md       (BMAD frontmatter)
       └── TECH_STACK.md    (BMAD frontmatter)
                │
                │  구현 안내 / Guides implementation
                ↓
       app/                 ← 실제 코드 / Runtime code
       ├── api/     (25+ 엔드포인트)
       ├── services/ (5개 서비스)
       ├── models/   (6개 테이블)
       └── ...
```

---

## 3. 9개 에이전트 / 9 Agent Personas

각 에이전트는 정의된 전문성, 책임, 출력 형식을 가진 전문 AI 페르소나입니다.

Each agent is a specialized AI persona with defined expertise, responsibilities, and output formats.

| # | 에이전트 / Agent | 이름 / Name | 역할 / Role | 본 프로젝트 사용 / Used |
|---|---|---|---|---|
| 1 | **분석가 / Analyst** | Mary | 프로젝트 컨텍스트, 요구사항 분석 / Project context, requirements analysis | ✅ Phase 0 |
| 2 | **PM** | John | PRD 작성, 기능 정의, 인수 기준 / PRD, features, acceptance criteria | ✅ PRD.md |
| 3 | **아키텍트 / Architect** | Winston | 시스템 설계, 기술 스택 / Architecture, tech stack decisions | ✅ ARCHITECTURE.md |
| 4 | **개발자 / Developer** | Amelia | Story 기반 코드 구현 (정식) / Formal story-driven implementation | ✅ Sprint 1-3 |
| 5 | **QA** | Quinn | 코드 리뷰, 보안/성능/호환성 검사 / Code review, security/perf checks | ✅ 리뷰 |
| 6 | **스크럼 마스터 / SM** | Bob | 스프린트 계획, Story 추적 / Sprint planning, story tracking | ✅ STORIES.md |
| 7 | **UX 디자이너** | Sally | 사용자 경험 설계 / User experience design | ✅ UI 설계 |
| 8 | **기술 작가 / Tech Writer** | Paige | 문서 작성 / Documentation | ✅ docs/ |
| 9 | **퀵플로우 개발자 / Quick-Flow Dev** | Barry | 빠른 사양→구현 (솔로) / Rapid spec→implementation | ✅ Sprint 4 |

### Barry vs Amelia (개발자 차이점 / Developer Difference)

| 비교 / Compare | **Barry** (퀵플로우) | **Amelia** (정식 개발) |
|---|---|---|
| 속도 / Speed | 빠름 / Fast | 체계적 / Methodical |
| 입력 / Input | 자유로운 요청 / Free-form request | 정식 Story 파일 필요 / Formal story spec file |
| 용도 / Use for | 작은 기능, 버그 수정, 빠른 변경 / Small features, bug fixes | 대형 기능, 새로운 시스템 / Large features, new systems |
| Sprint 4 사용 / Used in Sprint 4 | ✅ P0 K-drama Cosmos 마이그레이션 | — |

---

## 4. 워크플로우 4단계 / 4 Workflow Phases

BMAD는 개발을 4개의 워크플로우 단계로 구성합니다.

BMAD organizes development into 4 workflow phases.

```
Phase 0               Phase 1              Phase 2              Phase 3
분석 / Analysis        계획 / Planning       설계 / Solutioning    구현 / Implementation
─────────────────────────────────────────────────────────────────────────────

┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Mary     │────►│ John + Bob   │────►│ Winston      │────►│ Barry/Amelia │
│ 분석가    │     │ PM + SM      │     │ 아키텍트      │     │ + Quinn (QA) │
│          │     │              │     │              │     │ + Paige (작가)│
│ 출력:     │     │ 출력:         │     │ 출력:         │     │ 출력:         │
│ project- │     │ PRD.md       │     │ ARCH.md      │     │ 코드 + 테스트  │
│ context  │     │ STORIES.md   │     │ TECH_STACK   │     │ + 문서        │
│          │     │              │     │   .md        │     │              │
│ Output:  │     │ Output:      │     │ Output:      │     │ Output:      │
│ context  │     │ PRD+Stories  │     │ Arch+Tech    │     │ Code+Docs    │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 5. 실제 적용: 7단계 전체 실행 / Real Execution: 7-Step Full Workflow

2026년 3월 27일, 이 프로젝트에서 **BMAD 7단계를 모두 순서대로 실행**했습니다. 아래는 각 에이전트가 실제로 수행한 작업 기록입니다.

On March 27, 2026, we executed **all 7 BMAD steps in sequence** on this project. Below is the actual record of what each agent did.

### ① PM John — 스프린트 분석 / Sprint Analysis

```
입력:  Sprint 4 계획 요청
작업:  PRD 기반 Sprint 4 우선순위 분석
결과:  5개 항목 P0~P4 우선순위 정렬

Input:  Sprint 4 planning request
Work:   PRD-based Sprint 4 priority analysis
Output: 5 items prioritized P0–P4
  P0: K-drama Cosmos DB 마이그레이션
  P1: Admin CSV export
  P2: 발음 피드백 강화 / Pronunciation feedback
  P3: 진도 대시보드 개선 / Progress dashboard
  P4: 모바일 음성 UI / Mobile voice UI
```

### ② Architect Winston — 아키텍처 검증 / Architecture Validation

```
작업:  Sprint 4 모든 항목이 기존 아키텍처에 맞는지 검증
결과:  ✅ 전부 기존 설계 범위 내 — 새 인프라 불필요

Work:  Validated all Sprint 4 items fit existing architecture
Result: ✅ All within existing design — no new infrastructure needed
```

### ③ SM Bob — 스프린트 계획 / Sprint Planning

```
작업:  전체 10개 Epic, 25+ Story 상태 정리
출력:  _bmad-output/implementation-artifacts/sprint-status.yaml
  - Epic 1~4, 6~10: done ✅
  - Epic 5: in-progress (Story 5.3 대기)
  - Sprint 4: 5개 Story 배정

Work:  Full status of 10 epics, 25+ stories
Output: sprint-status.yaml
  - Epics 1-4, 6-10: done ✅
  - Epic 5: in-progress (Story 5.3 pending)
  - Sprint 4: 5 stories assigned
```

### ④ Barry (퀵플로우 개발) — P0 구현 / P0 Implementation

```
작업 1: scripts/seed_drama_cosmos.py 작성
  - business_korean.json → Cosmos DB drama_content 컨테이너 시딩
  - uuid5 결정적 ID (upsert 안전)
  - 8개 드라마 대화 문서

작업 2: mcp_server/server.py 수정
  - get_drama_dialogue() → async 변환
  - Cosmos DB 우선 조회 → JSON 파일 폴백
  - 두 가지 필드명 호환 (drama / drama_name)

Work 1: Created scripts/seed_drama_cosmos.py
  - Seeds drama_dialogues from JSON to Cosmos DB
  - Deterministic uuid5 IDs for safe upsert
  - 8 drama dialogue documents

Work 2: Modified mcp_server/server.py
  - get_drama_dialogue() → converted to async
  - Cosmos DB first → JSON file fallback
  - Compatible with both field names (drama / drama_name)
```

### ⑤ QA Quinn — 코드 리뷰 / Code Review

```
검토 파일 6개:
  ✅ startup.sh        — ffmpeg 설치 (멱등, || true)
  ✅ app/core/redis.py  — 자격 증명 마스킹 (_mask_url)
  ✅ app/api/chat.py    — 진단 엔드포인트
  ✅ speech_service.py  — 폴백 경고 개선
  ✅ mcp_server/server.py — async Cosmos + JSON 폴백
  ✅ seed_drama_cosmos.py — 결정적 uuid5, 정리 완료

보안 검사:
  ✅ 로그에 비밀번호 노출 없음 (_mask_url)
  ✅ SQL 인젝션 위험 없음 (파라미터화 쿼리)
  ✅ 시스템 호출에 사용자 입력 직접 전달 없음

Reviewed 6 files:
  ✅ startup.sh       — ffmpeg install (idempotent, || true)
  ✅ app/core/redis.py — credential masking (_mask_url)
  ✅ app/api/chat.py   — diagnostics endpoint
  ✅ speech_service.py — fallback warning improvement
  ✅ mcp_server/server.py — async Cosmos + JSON fallback
  ✅ seed_drama_cosmos.py — deterministic uuid5, proper cleanup

Security:
  ✅ No credentials in logs
  ✅ No SQL injection risk (parameterized queries)
  ✅ No user input in system calls
```

### ⑥ Tech Writer Paige — 문서 업데이트 / Documentation Update

```
업데이트 파일:
  - docs/CODEBASE.md: MCP 도구 7번 Cosmos DB 설명 추가
  - docs/CODEBASE.md: seed_drama_cosmos.py 스크립트 추가
  - docs/CODEBASE.md: startup.sh ffmpeg 설명 갱신

Updated files:
  - docs/CODEBASE.md: MCP tool 7 Cosmos DB note added
  - docs/CODEBASE.md: seed_drama_cosmos.py script added
  - docs/CODEBASE.md: startup.sh ffmpeg description updated
```

### ⑦ 구현 준비 검증 / Implementation Readiness Check

```
검증 결과 (5개 기준):
  A. 기능 커버리지    ⚠️ PASS (PRD 3.2 텍스트 채팅에 공식 Story 없음)
  B. 아키텍처 커버리지 ✅ PASS (전체 대응)
  C. 기술 일관성      ✅ PASS (4개 문서 일치)
  D. Story 완성도    ⚠️ PASS (27개 정식 Story 완료, Sprint 4 항목은 약식)
  E. 스프린트 상태    ✅ Sprint 4 진행 중 (P0 완료)

Validation results (5 criteria):
  A. Feature Coverage    ⚠️ PASS (PRD 3.2 Text Chat has no formal story)
  B. Architecture Coverage ✅ PASS (full alignment)
  C. Technology Consistency ✅ PASS (all 4 docs agree)
  D. Story Completeness   ⚠️ PASS (27 formal stories done; Sprint 4 items informal)
  E. Sprint Status        ✅ Sprint 4 in progress (P0 complete)
```

---

## 6. 스프린트 이력 / Sprint History

| 스프린트 / Sprint | 이름 / Name | 내용 / Content | 상태 / Status |
|---|---|---|---|
| **Sprint 1** | 핵심 음성 + 채팅 / Core Voice + Chat | WebSocket 음성, AI 에이전트, 프론트엔드 UI / WebSocket voice, AI agent, Frontend | ✅ 완료 / Done |
| **Sprint 2** | Cosmos DB 통합 / Integration | 코어 레이어, 대화 마이그, 학습 이벤트 / Core layer, conversation migration, events | ✅ 완료 / Done |
| **Sprint 3** | 인증 + 관리자 / Auth + Admin | 이메일 인증, Entra ID, 관리자 대시보드, Redis 진단 / Email verification, Entra ID, admin, Redis | ✅ 완료 / Done |
| **Sprint 4** | 콘텐츠 + 폴리시 / Content & Polish | K-drama Cosmos (P0 ✅), CSV 내보내기, 발음, 모바일 / K-drama Cosmos (P0 ✅), CSV, pronunciation, mobile | 🚀 진행 중 / In Progress |

### 스프린트별 Epic 현황 / Epic Status by Sprint

| Epic | 이름 / Name | 스프린트 / Sprint | 상태 / Status |
|---|---|---|---|
| Epic 1 | 음성 / Voice | 1 | ✅ done (4 stories) |
| Epic 2 | 교육 콘텐츠 / Teaching Content | 1 | ✅ done (3 stories) |
| Epic 3 | Azure 인프라 / Infrastructure | 1-2 | ✅ done (2 stories) |
| Epic 4 | 학습 관리 / Learning Management | 2 | ✅ done (4 stories) |
| Epic 5 | Cosmos DB | 2, 4 | ✅ done (4 stories — 5.3 Sprint 4에서 완료) |
| Epic 6 | 인증 / Authentication | 3 | ✅ done (4 stories) |
| Epic 7 | 관리자 / Admin | 3 | ✅ done (2 stories) |
| Epic 8 | MCP 도구 / Tools | 2 | ✅ done (1 story) |
| Epic 9 | PWA | 3 | ✅ done (1 story) |
| Epic 10 | 프로덕션 탄력성 / Resilience | 4 | ✅ done (2 stories) |

---

## 7. 44개 스킬 참조 / 44 Skills Reference

BMAD v6.2.2에는 VS Code Copilot Chat에서 호출할 수 있는 **44개의 재사용 가능한 스킬**이 포함됩니다. 스킬 파일은 `.github/skills/`에 있습니다.

BMAD v6.2.2 includes **44 reusable skills** invokable in VS Code Copilot Chat. Files in `.github/skills/`.

### 분석 스킬 / Analysis Skills
| 스킬 / Skill | 트리거 / Trigger | 설명 / Description |
|-------|---------|-------------|
| `bmad-document-project` | "document this project" | 브라운필드 프로젝트 AI 컨텍스트 생성 / Scan project for AI context |
| `bmad-domain-research` | "domain research for [topic]" | 도메인/산업 연구 / Domain/industry research |
| `bmad-market-research` | "market research" | 경쟁/고객 분석 / Competition and customer analysis |
| `bmad-technical-research` | "technical research" | 기술/아키텍처 연구 / Technology research |
| `bmad-generate-project-context` | "generate project context" | project-context.md 생성 / Create project-context.md |

### 계획 스킬 / Planning Skills
| 스킬 / Skill | 트리거 / Trigger | 설명 / Description |
|-------|---------|-------------|
| `bmad-create-prd` | "create PRD" | 제품 요구사항 문서 작성 / Create PRD |
| `bmad-edit-prd` | "edit this PRD" | 기존 PRD 수정 / Modify existing PRD |
| `bmad-validate-prd` | "validate this PRD" | PRD 검증 / Check PRD against standards |
| `bmad-product-brief` | "create product brief" | 제품 브리프 작성 / Create/update product briefs |
| `bmad-create-epics-and-stories` | "create epics and stories" | 요구사항 → Story 분해 / Break requirements into stories |
| `bmad-create-story` | "create story [id]" | 개별 Story 파일 생성 / Create individual story file |

### 설계 스킬 / Solutioning Skills
| 스킬 / Skill | 트리거 / Trigger | 설명 / Description |
|-------|---------|-------------|
| `bmad-create-architecture` | "create architecture" | 시스템 아키텍처 설계 / Design system architecture |
| `bmad-create-ux-design` | "create UX design" | UX 패턴 및 사양 계획 / Plan UX patterns and specs |
| `bmad-check-implementation-readiness` | "check readiness" | 사양 완성도 검증 / Validate all specs complete |

### 구현 스킬 / Implementation Skills
| 스킬 / Skill | 트리거 / Trigger | 설명 / Description |
|-------|---------|-------------|
| `bmad-quick-dev` | "build/fix/add [feature]" | 빠른 사양 → 코드 / Rapid spec → code |
| `bmad-dev-story` | "dev story [file]" | Story 파일 기반 구현 / Story-driven implementation |
| `bmad-code-review` | "review this code" | 3중 적대적 코드 리뷰 / 3-layer adversarial review |
| `bmad-qa-generate-e2e-tests` | "create qa tests" | E2E 테스트 생성 / Generate end-to-end tests |

### 스프린트 관리 / Sprint Management
| 스킬 / Skill | 트리거 / Trigger | 설명 / Description |
|-------|---------|-------------|
| `bmad-sprint-planning` | "run sprint planning" | Epic에서 스프린트 계획 생성 / Generate sprint plan |
| `bmad-sprint-status` | "check sprint status" | 스프린트 상태 요약 + 리스크 / Summarize + surface risks |
| `bmad-correct-course` | "correct course" | 스프린트 중 방향 수정 / Manage sprint changes |
| `bmad-retrospective` | "run retrospective" | Epic 후 회고 / Post-epic lessons learned |

### 리뷰 & 편집 / Review & Editing
| 스킬 / Skill | 트리거 / Trigger | 설명 / Description |
|-------|---------|-------------|
| `bmad-review-adversarial-general` | "critical review" | 냉소적 적대적 리뷰 / Cynical adversarial review |
| `bmad-review-edge-case-hunter` | "edge case analysis" | 경계 조건 감사 / Boundary condition audit |
| `bmad-editorial-review-prose` | "review prose" | 문체 편집 / Copy-editing for communication |
| `bmad-editorial-review-structure` | "structural review" | 구조 재편 / Document reorganization |

### 유틸리티 / Utility Skills
| 스킬 / Skill | 트리거 / Trigger | 설명 / Description |
|-------|---------|-------------|
| `bmad-brainstorming` | "help me brainstorm" | 창의적 아이디어 세션 / Creative ideation sessions |
| `bmad-advanced-elicitation` | (개선 요청) | LLM 출력 품질 향상 / Improve LLM output |
| `bmad-distillator` | "distill documents" | 무손실 압축 / Lossless compression |
| `bmad-shard-doc` | "shard document" | 대형 문서 분할 / Split large docs |
| `bmad-index-docs` | "create docs index" | index.md 생성 / Generate index.md |
| `bmad-party-mode` | "party mode" | 멀티 에이전트 그룹 토론 / Multi-agent discussion |
| `bmad-help` | "what should I do next" | 다음 행동 추천 / Recommend next action |
| `bmad-init` | (자동) | BMAD 설정 초기화 / Initialize configuration |

---

## 8. 산출물 / Output Artifacts

### 계획 산출물 (bmad-docs/) / Planning Artifacts

| 문서 / Document | 에이전트 / Agent | 내용 요약 / Summary |
|---|---|---|
| **PRD.md** | PM John | 비전, 2 페르소나, 10개 기능, 인증 전략, API 요약 / Vision, 2 personas, 10 features, auth, API |
| **ARCHITECTURE.md** | Architect Winston | 10개 섹션: 컨텍스트, 인증, 음성, DB, 캐시, 이메일, 관리자 / 10 sections: context, auth, voice, DB, cache, email, admin |
| **STORIES.md** | SM Bob | 10 Epic, 25+ Story, 인수 기준 포함, 4 스프린트 이력 / 10 epics, 25+ stories with ACs, 4 sprint history |
| **TECH_STACK.md** | Architect Winston | 런타임, Azure 서비스, 시스템 의존성, 코드 규칙 / Runtime, Azure services, system deps, conventions |

모든 BMAD 산출물에는 **프론트매터 메타데이터**가 포함됩니다.

All BMAD artifacts include **frontmatter metadata**:

```yaml
---
stepsCompleted: [완료된 워크플로우 단계 목록]
inputDocuments: [참조한 소스 문서]
workflowType: 'prd' | 'architecture' | 'epics-and-stories'
bmadAgent: 'Agent Name'
bmadVersion: '6.2.2'
lastUpdated: '2026-03-27'
---
```

### 구현 산출물 (_bmad-output/) / Implementation Artifacts

| 문서 / Document | 용도 / Purpose |
|---|---|
| `sprint-status.yaml` | 전체 스프린트 추적 (10 Epic, 25+ Story 상태) / Full sprint tracking |

### 프로젝트 문서 (docs/) / Project Documentation

| 문서 / Document | 에이전트 / Agent | 내용 / Content |
|---|---|---|
| `BMAD.md` | Paige (기술 작가) | 이 문서 — BMAD 방법론 / This file — BMAD methodology |
| `CODEBASE.md` | Paige | 파일 트리 + 엔드포인트 / File tree + endpoints |
| `AI_ENGINE.md` | Paige | AI Foundry + MCP 도구 / AI Foundry + MCP tools |
| `DATABASE.md` | Paige | PostgreSQL + Cosmos DB |
| `NETWORK.md` | Paige | VNet + 프라이빗 엔드포인트 / Private endpoints |
| `OPERATIONS.md` | Paige | 배포 + 시작 / Deployment + startup |
| `SECURITY.md` | Paige | 인증 + OWASP / Auth + OWASP |
| `ADMIN_API_REFERENCE.md` | Paige | 관리자 API 문서 / Admin API docs |
| `ADMIN_DASHBOARD.md` | Paige | 대시보드 UI 문서 / Dashboard UI docs |
| `DEVELOPMENT_JOURNAL.md` | Paige | 개발 일지 / Development history |

---

## 9. 프레임워크 구조 / Framework Structure

```
_bmad/                              # BMAD 프레임워크 루트 (v6.2.2) / Framework root
│
├── _config/                        # 설정 / Configuration
│   ├── manifest.yaml               # 프레임워크 매니페스트 / Framework manifest
│   ├── agent-manifest.csv          # 9개 에이전트 / All 9 agents
│   ├── skill-manifest.csv          # 44개 스킬 / All 44 skills
│   ├── workflow-manifest.csv       # 워크플로우 정의 / Workflow definitions
│   ├── files-manifest.csv          # 파일 참조 / File references
│   ├── bmad-help.csv              # 도움말 색인 / Help index
│   └── agents/                    # 에이전트 커스터마이징 (.yaml) / Agent customizations
│
├── _memory/                       # 영구 컨텍스트 / Persistent context
│   ├── config.yaml
│   └── tech-writer-sidecar/       # 기술 작가 표준 / Tech writer standards
│
├── core/                          # 코어 BMAD 모듈 / Core modules
│   ├── config.yaml
│   ├── skills/                    # 공유 스킬 / Shared skills
│   └── tasks/                     # 공유 태스크 / Shared tasks
│
└── bmm/                           # 비즈니스 메소드 모듈 / Business Method Module
    ├── config.yaml                # 프로젝트 설정 / Project config:
    │     project_name: korean-biz-agent
    │     user_name: Aimee
    │     communication_language: English
    │     document_output_language: English
    │     user_skill_level: intermediate
    │
    ├── agents/                    # 9개 에이전트 정의 (.md) / Agent definitions
    └── workflows/                 # 4단계 워크플로우 / Phase workflows
        ├── 1-analysis/            # 분석 / Analysis
        ├── 2-plan-workflows/      # 계획 / Planning
        ├── 3-solutioning/         # 설계 / Solutioning
        └── 4-implementation/      # 구현 / Implementation
```

---

## 10. BMAD 호출 방법 / How to Invoke BMAD

### VS Code Copilot Chat에서 / In VS Code Copilot Chat

BMAD 스킬은 `.github/skills/`에 VS Code Copilot 스킬로 설치되어 있습니다.

BMAD skills are installed as VS Code Copilot skills in `.github/skills/`.

```
# 에이전트 호출 / Agent invocation
"Talk to John"          → PM (PRD 작성/편집 / PRD creation/editing)
"Talk to Winston"       → 아키텍트 (시스템 설계 / system design)
"Talk to Bob"           → 스크럼 마스터 (스프린트 계획 / sprint planning)
"Talk to Barry"         → 퀵플로우 개발 (빠른 구현 / rapid implementation)
"Talk to Quinn"         → QA (코드 리뷰 / code review)
"Talk to Paige"         → 기술 작가 (문서 / documentation)
"Talk to Amelia"        → 개발자 (Story 기반 구현 / story-driven dev)
"Talk to Sally"         → UX 디자이너 (UI 설계 / UI design)
"Talk to Mary"          → 분석가 (요구사항 분석 / requirements analysis)

# 스킬 호출 / Skill invocation
"create PRD"                   → bmad-create-prd
"create architecture"          → bmad-create-architecture
"create epics and stories"     → bmad-create-epics-and-stories
"run sprint planning"          → bmad-sprint-planning
"check sprint status"          → bmad-sprint-status
"review this code"             → bmad-code-review (3중 적대적 리뷰 / 3-layer review)
"document this project"        → bmad-document-project
"what should I do next"        → bmad-help (다음 행동 추천 / recommend next)
"party mode"                   → 멀티 에이전트 그룹 토론 / Multi-agent discussion
"check implementation readiness" → 구현 준비 검증 / Validate specs
```

### 마이크로 파일 아키텍처 / Step-File Architecture

BMAD 워크플로우는 **마이크로 파일 아키텍처**를 사용합니다 — 각 단계가 별도 마크다운 파일로 순차 로딩됩니다.

BMAD workflows use **micro-file architecture** — each step is a separate markdown file loaded sequentially.

```
bmad-create-prd/
├── SKILL.md           # 스킬 정의 / Skill definition
├── workflow.md        # 진입점 (설정 로드, 단계 라우팅) / Entry point
├── steps-c/           # 생성 모드 단계 / Create mode steps
│   ├── step-01-init.md
│   ├── step-02-discovery.md
│   └── ...
└── templates/
    └── prd-template.md  # 프론트매터 포함 출력 템플릿 / Output template
```

**규칙 / Rules**: 한 번에 한 단계 → 완료 후 다음 로딩 → 프론트매터에 상태 저장 → 사용자 승인 기반 진행

One step at a time → Complete before next → State in frontmatter → User approval for progression

---

## 탐색 / Navigation

| 다음 / Next | 문서 / Document |
|---|---|
| 메인 README / Main README | → [README.md](../README.md) |
| AI 작동 방식 / How AI works | → [AI_ENGINE.md](AI_ENGINE.md) |
| 데이터베이스 / Database | → [DATABASE.md](DATABASE.md) |
| 네트워크 / Network | → [NETWORK.md](NETWORK.md) |
| 코드베이스 / Codebase | → [CODEBASE.md](CODEBASE.md) |
| 보안 / Security | → [SECURITY.md](SECURITY.md) |
| 운영 / Operations | → [OPERATIONS.md](OPERATIONS.md) |
| 개발 일지 / Dev Journal | → [DEVELOPMENT_JOURNAL.md](DEVELOPMENT_JOURNAL.md) |
