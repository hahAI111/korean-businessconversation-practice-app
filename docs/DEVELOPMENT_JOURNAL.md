# 🛠️ Development Journal — AI-Assisted Full-Stack Project Build
# 🛠️ 개발 일지 — AI로 풀스택 프로젝트를 처음부터 구축한 전체 기록
# 🛠️ 开发日志 — 用 AI 从零构建全栈项目的完整记录

> **How I built two production Azure applications using Claude (via GitHub Copilot) as my co-developer**
>
> **Claude(GitHub Copilot)를 공동 개발자로 사용하여 두 개의 Azure 프로덕션 애플리케이션을 구축한 방법**
>
> **我如何用 Claude（通过 GitHub Copilot）作为搭档，从零构建两个 Azure 生产应用**

---

## Table of Contents / 목차 / 目录

1. [Background / 배경 / 项目背景](#1-background--배경--项目背景)
2. [Development Timeline / 개발 타임라인 / 开发流程全览](#2-development-timeline--개발-타임라인--开发流程全览)
3. [Pitfalls & Bugs / 함정 & 버그 / 踩过的坑](#3-pitfalls--bugs--함정--버그--踩过的坑)
4. [Prompt Techniques / 프롬프트 기법 / Prompt 技巧](#4-prompt-techniques--프롬프트-기법--prompt-技巧)
5. [What AI Couldn't Do / AI가 못한 것 / AI 搞不定的事](#5-what-ai-couldnt-do--ai가-못한-것--ai-搞不定的事)
6. [Key Lessons / 핵심 교훈 / 关键经验总结](#6-key-lessons--핵심-교훈--关键经验总结)
7. [Tool Chain / 도구 체인 / 工具链](#7-tool-chain--도구-체인--工具链)

---

## 1. Background / 배경 / 项目背景

**My Role / 역할 / 我的角色**：
- EN: Azure AI Support Engineer at Microsoft. Not a CS major.
- KR: Microsoft Azure AI 지원 엔지니어. 컴퓨터공학 전공 아님.
- CN: 微软 Azure AI 技术支持工程师，非科班程序员出身。

**Goal / 목표 / 目标**：
- EN: Build two full-stack projects and deploy them to Azure production — using AI as my co-developer.
- KR: AI를 공동 개발자로 활용하여 두 개의 풀스택 프로젝트를 구축하고 Azure 프로덕션에 배포.
- CN: 利用工作间隙，用 AI 辅助编程，独立完成两个全栈项目并部署到 Azure 生产环境。

**Two Projects / 두 프로젝트 / 两个项目**：
- **Korean Business Conversation Practice App** — AI Korean business conversation practice (FastAPI + GPT-5-nano + Voice) / AI 한국어 비즈니스 회화 연습 / AI 韩语商务会话练习
- **AimeeWang Portfolio** — Personal portfolio + blog + analytics dashboard (Flask + PostgreSQL) / 개인 포트폴리오 + 블로그 + 분석 대시보드 / 个人作品集 + 博客 + 数据分析后台

**My AI Partner / AI 파트너 / 我的 AI 搭档**：
- EN: GitHub Copilot (Claude model) in VS Code. I gave instructions through conversation; it wrote code, debugged, deployed, and documented.
- KR: VS Code의 GitHub Copilot (Claude 모델). 대화로 지시하면 코드 작성, 디버깅, 배포, 문서화를 수행.
- CN: VS Code 里的 GitHub Copilot（Claude 模型），通过对话下指令，它帮我写代码、调试、部署、写文档。

---

## 2. Development Timeline / 개발 타임라인 / 开发流程全览

### Phase 1: Feature Development / 기능 개발 / 功能开发

| Feature / 기능 / 功能 | My Prompt (approx.) / 내 지시 / 我的指令 | What AI Did / AI가 한 일 / AI 做了什么 |
|---|---|---|
| **Premium UI Redesign** | "Change UI to premium gold + navy style" / "프리미엄 골드 + 네이비 스타일로 바꿔" / "把 UI 改成 premium gold + navy 风格" | Rewrote style.css, updated all HTML color schemes / style.css 재작성, 전체 HTML 배색 변경 / 重写 style.css，改了所有 HTML 配色 |
| **Learning Check-in (打卡)** | "Add a daily check-in feature" / "학습 체크인 기능 추가해" / "加一个学习打卡功能" | Added streak API, check-in button, DB table / streak API, 체크인 버튼, DB 테이블 추가 / 加了 streak API、打卡按钮、数据库表 |
| **Vocabulary CRUD** | "Add a vocab management page" / "단어장 관리 페이지 추가해" / "加词汇管理页面" | Created vocab.html, API routes, DB operations / vocab.html, API 라우트, DB 작업 생성 / 新建 vocab.html、API 路由、数据库操作 |
| **Voice Chat** | "Add voice feature, WebSocket" / "음성 기능 추가, WebSocket" / "加语音功能，WebSocket" | Implemented /ws/voice, Azure Speech SDK, SSML config / /ws/voice, Azure Speech SDK, SSML 구성 구현 / 实现 /ws/voice、Azure Speech SDK、SSML 配置 |
| **Multi-language Voice** | "Voice input should support any language, not just Korean" / "음성 입력은 한국어뿐만 아니라 모든 언어 지원" / "语音输入支持任何语言，不只韩语" | Changed STT from "ko-KR" to "auto", updated Agent instructions / STT를 "ko-KR"에서 "auto"로 변경 / 改 STT 从 "ko-KR" 到 "auto" |
| **PWA** | "Make it a PWA, installable on phone" / "PWA로 만들어, 폰에 설치 가능하게" / "做成 PWA，能装到手机桌面" | Created manifest.json, service-worker.js, offline page / manifest.json, service-worker.js, 오프라인 페이지 생성 / 创建 manifest.json、service-worker.js、离线页面 |

### Phase 2: Performance Optimization / 성능 최적화 / 性能优化

| Problem / 문제 / 问题 | My Description / 내 설명 / 我的描述 | AI Diagnosis & Fix / AI 진단 & 수정 / AI 诊断 & 修复 |
|---|---|---|
| 10-20s response time / 응답 10-20초 / 对话回复 10-20 秒 | "Too slow, bad UX" / "너무 느려, UX 최악" / "太慢了，用户体验很差" | (1) GPT-5.2 → gpt-5-nano (2) Removed inline TTS (3) asyncio.to_thread (4) 1→2 workers |
| Slow HTTP connections / HTTP 연결 느림 / HTTP 连接慢 | AI found this itself / AI가 자체 발견 / AI 自己发现的 | Added module-level connection pools `_http_pool`, `_tts_pool` / 모듈 레벨 연결 풀 추가 / 加了连接池 |
| Cache misses / 캐시 미스 / 缓存未命中 | AI found this itself / AI가 자체 발견 / AI 自己发现的 | Fire-and-forget async saves / 비동기 저장으로 응답 차단 제거 / fire-and-forget 异步保存 |

### Phase 3: Deployment & DevOps / 배포 & DevOps / 部署 & DevOps

| Step / 단계 / 阶段 | What / 내용 / 做了什么 |
|---|---|
| Clean junk files / 정크 파일 정리 / 清理垃圾文件 | Deleted temp files, caches, unused dirs / 임시 파일, 캐시, 미사용 디렉토리 삭제 / 删除临时文件、缓存、无用目录 |
| Remove secrets / 시크릿 제거 / 移除密码 | README (9), ARCHITECTURE (3), config.py (1) → placeholders / README (9건), ARCHITECTURE (3건), config.py (1건) → 플레이스홀더 / README 9处 → 占位符 |
| Create .env.example / .env.example 생성 / 创建 .env.example | Safe environment variable template / 안전한 환경 변수 템플릿 / 安全的环境变量模板 |
| Git init + push / Git 초기화 + 푸시 / Git 初始化 + 推送 | Public showcase repo / 공개 전시 repo / 公开展示 repo |
| Private production repo / 비공개 프로덕션 repo / 创建私有生产 repo | OIDC + GitHub Actions CI/CD |
| GitHub Secrets / GitHub 시크릿 설정 | 7 secrets via `gh secret set` / `gh secret set`으로 7개 시크릿 설정 / 7 个 secrets 一键设好 |
| my-website dual repo / my-website 이중 repo / my-website 双 repo | aimeewebpage (private/production) + my-website-profile (public/showcase) |

### Phase 4: Documentation / 문서화 / 文档

| Document / 문서 / 文档 | Content / 내용 / 内容 | Languages / 언어 / 语言 |
|---|---|---|
| README.md | Project overview, architecture diagram / 프로젝트 개요, 아키텍처 다이어그램 / 项目总览、架构图 | EN+KR |
| docs/CODEBASE.md | Complete file & folder map / 전체 파일 & 폴더 맵 / 全部文件地图 | EN+KR |
| docs/AI_ENGINE.md | AI engine deep dive / AI 엔진 심층 분석 / AI 引擎深度解析 | EN+KR |
| docs/DATABASE.md | Data architecture / 데이터 아키텍처 / 数据架构 | EN+KR |
| docs/NETWORK.md | API + WebSocket + Auth / API + WebSocket + 인증 / API + WebSocket + 认证 | EN+KR |
| docs/BMAD.md | BMAD methodology / BMAD 방법론 / BMAD 方法论 | EN+KR |
| docs/OPERATIONS.md | Operations guide / 운영 가이드 / 运维指南 | EN+KR+CN |
| docs/SECURITY.md | Secrets & security / 시크릿 & 보안 / 密钥安全架构 | EN+KR+CN |

---

## 3. Pitfalls & Bugs / 함정 & 버그 / 踩过的坑

### 🔴 Pitfall 1: Wrong Deploy Command → 503 Crash / 잘못된 배포 명령 → 503 충돌 / 部署方式错误 → 503 崩溃

**Symptom / 증상 / 现象**：
- EN: Website 503 after deployment, log shows `No module named uvicorn`.
- KR: 배포 후 503 오류, 로그에 `No module named uvicorn` 표시.
- CN: 部署后网站 503，日志 `No module named uvicorn`。

**Root Cause / 원인 / 原因**：
- EN: Used wrong command `az webapp deploy --type zip` which overwrites the entire `/home/site/wwwroot/` including Python virtual environment `antenv/`.
- KR: 잘못된 명령 `az webapp deploy --type zip` 사용 — `/home/site/wwwroot/` 전체를 덮어씀 (Python 가상환경 `antenv/` 포함).
- CN: 用了错误的命令 `az webapp deploy --type zip`，会覆盖整个目录，包括 Python 虚拟环境 `antenv/`。

```bash
# ❌ WRONG (destroys virtual environment / 가상환경 파괴 / 会破坏虚拟环境)
az webapp deploy --type zip --src deploy.zip

# ✅ CORRECT (Oryx auto pip install / Oryx 자동 pip install / Oryx 会自动 pip install)
az webapp deployment source config-zip --src deploy.zip
```

**Lesson / 교훈 / 教训**：
- EN: Azure has two zip deploy methods with similar names but completely different behavior. Cost hours to figure out.
- KR: Azure에는 이름은 비슷하지만 동작이 완전히 다른 두 가지 zip 배포 방식이 있음. 해결에 몇 시간 소요.
- CN: Azure 有两种 zip 部署方式，名字很像但行为完全不同。这个坑花了好几个小时。

---

### 🔴 Pitfall 2: Special Characters in DB Password / DB 비밀번호 특수문자 / 数据库密码特殊字符

**Symptom / 증상 / 现象**：
- EN: Can't connect to PostgreSQL, authentication failure.
- KR: PostgreSQL 연결 불가, 인증 실패.
- CN: 连不上 PostgreSQL，报认证失败。

**Root Cause / 원인 / 原因**：
- EN: Password contains `!` which is a special character in URLs. Must URL-encode as `%21`.
- KR: 비밀번호에 `!`가 포함되어 있으며, URL에서 특수문자이므로 `%21`로 인코딩 필요.
- CN: 密码含 `!`，在 URL 里是特殊字符，必须编码为 `%21`。

```
# ❌ postgresql+asyncpg://user:Aimee2026Pg!@host:5432/db
# ✅ postgresql+asyncpg://user:Aimee2026Pg%21@host:5432/db
```

---

### 🔴 Pitfall 3: CI/CD Failed 3 Times in a Row / CI/CD 3연속 실패 / CI/CD 连续失败 3 次

**Failure 1 / 실패 1 / 第 1 次**：`No module named pytest`
- EN: Workflow ran tests but didn't install pytest. Fix: added `pip install pytest pytest-asyncio httpx`.
- KR: 워크플로우가 테스트를 실행했지만 pytest 미설치. 수정: `pip install pytest pytest-asyncio httpx` 추가.
- CN: workflow 跑测试但没装 pytest。修复：加了 `pip install pytest pytest-asyncio httpx`。

**Failure 2 / 실패 2 / 第 2 次**：`ERROR: file or directory not found: tests/`
- EN: No `tests/` directory in the project. Fix: added conditional skip logic.
- KR: 프로젝트에 `tests/` 디렉토리 없음. 수정: 조건부 스킵 로직 추가.
- CN: 项目里没有 tests/ 目录。修复：加了判断逻辑，没有就跳过。

**Failure 3 / 성공 / 第 3 次**：✅ Success!

**Lesson / 교훈 / 教训**：
- EN: Don't assume local environment = CI environment. Always simulate first.
- KR: 로컬 환경 = CI 환경이라고 가정하지 말 것. 항상 먼저 시뮬레이션.
- CN: 不要假设本地有的东西 CI 环境都有。

---

### 🟡 Pitfall 4: Corporate Policy Blocked Service Principal / 회사 정책이 서비스 주체 차단 / 公司策略阻止 Service Principal

**Symptom / 증상 / 现象**：`Credential lifetime exceeds the max value allowed`

**Solution / 해결 / 解决**：
- EN: Switched to **OIDC Federated Credentials** — no long-lived passwords needed.
- KR: **OIDC 연합 자격 증명**으로 전환 — 장기 비밀번호 불필요.
- CN: 改用 **OIDC 联合凭证**，不需要长期密码。

```
1. Create App Registration / 앱 등록 생성 / 创建 App Registration
2. Create Service Principal + assign Contributor / SP 생성 + Contributor 할당 / 创建 SP + 分配 Contributor
3. Add Federated Credential (trust GitHub OIDC) / 연합 자격 증명 추가 / 添加 Federated Credential
4. GitHub Secrets: only Client ID, Tenant ID, Subscription ID (no passwords!)
```

---

### 🟡 Pitfall 5: PowerShell Eats JSON Quotes / PowerShell이 JSON 따옴표 삼킴 / PowerShell 吞掉 JSON 引号

**Symptom / 증상 / 现象**：`az ad app federated-credential create --parameters '{...}'` → JSON parse error

**Fix / 수정 / 修复**：
- EN: Write JSON to a temp file, then `--parameters fedcred.json`. PowerShell + Azure CLI + inline JSON = quote hell.
- KR: JSON을 임시 파일에 쓴 후 `--parameters fedcred.json` 사용. PowerShell + Azure CLI + 인라인 JSON = 따옴표 지옥.
- CN: 把 JSON 写到临时文件，然后 `--parameters fedcred.json`。PowerShell + Azure CLI + JSON = 引号地狱。

---

### 🟡 Pitfall 6: GitHub CLI Not Found After Install / GitHub CLI 설치 후 인식 불가 / GitHub CLI 安装后找不到

**Symptom / 증상 / 现象**：`winget install GitHub.cli` succeeded, but `gh: not recognized`

**Fix / 수정 / 修复**：PATH not refreshed. Run: / PATH 미갱신. 실행: / PATH 没刷新，运行：
```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + 
            ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

---

### 🟡 Pitfall 7: Voice Only Recognized Korean / 음성이 한국어만 인식 / 语音只能识别韩语

**Fix / 수정 / 修复**：
- EN: Changed STT language from `"ko-KR"` to `"auto"` (multi-language auto-detect). Also updated Agent's VOICE_INSTRUCTIONS to accept any language input.
- KR: STT 언어를 `"ko-KR"`에서 `"auto"`(다국어 자동 감지)로 변경. Agent의 VOICE_INSTRUCTIONS도 모든 언어 입력 허용으로 업데이트.
- CN: 改 STT 从 `"ko-KR"` 到 `"auto"`（多语言自动检测），同时更新 Agent 指令。

---

### 🟢 Minor: pip install in startup.sh / startup.sh에서 pip install / startup.sh 里 pip install

**Symptom / 증상 / 现象**：
- EN: App Service startup timeout (>300s) because `startup.sh` installed a 200+MB package every time.
- KR: startup.sh가 매번 200+MB 패키지를 설치하여 App Service 시작 타임아웃 (>300초).
- CN: App Service 启动超时（>300 秒），因为 `startup.sh` 里每次启动都装 200+MB 的包。

**Fix / 수정 / 修复**：
- EN: Move all dependencies to `requirements.txt`, let Oryx build install once. `startup.sh` only starts uvicorn.
- KR: 모든 의존성을 `requirements.txt`로 이동, Oryx 빌드가 한 번만 설치. `startup.sh`는 uvicorn 시작만 담당.
- CN: 所有依赖放到 `requirements.txt`，Oryx 只装一次，`startup.sh` 只启动 uvicorn。

---

## 4. Prompt Techniques / 프롬프트 기법 / Prompt 技巧

### ✅ Effective Prompts / 효과적인 프롬프트 / 有效的指令

| My Prompt / 내 프롬프트 / 我的指令 | Why It Works / 왜 효과적인가 / 为什么有效 |
|---|---|
| "Change UI to premium gold + navy style" / "UI를 프리미엄 골드+네이비로 바꿔" / "把 UI 改成 gold + navy 风格" | Short & clear. AI knows exactly what to change. / 짧고 명확. AI가 정확히 무엇을 바꿀지 앎. / 简短明确，AI 立刻知道改什么。 |
| "Too slow, 10-20s, bad UX" / "너무 느려, 10-20초, UX 나빠" / "太慢了，10-20秒，体验很差" | Describe symptom + impact. Let AI diagnose root cause. / 증상 + 영향 설명. AI가 근본 원인 진단. / 描述现象+影响，让 AI 自己诊断。 |
| "Set this up the same way for my-website" / "my-website도 같은 방식으로 설정해" / "这个也帮我设置一样的" | Reference completed work as template. / 완성된 작업을 템플릿으로 참조. / 引用已完成的工作作为模板。 |
| "Can you do it for me?" / "네가 해줘" / "你可以帮我 set 吗" | When AI lists manual steps, tell it to just do it. It can run commands! / AI가 수동 단계를 나열할 때, 직접 하라고 지시. 명령 실행 가능! / AI 列出手动步骤时，直接让它代劳。 |
| "Write docs in CN+EN+KR" / "문서를 중영한 3개 국어로 작성해" / "写文档，中英韩三语" | Specify language requirements clearly. / 언어 요구사항을 명확히 지정. / 明确语言要求。 |

### ❌ Ineffective Prompts / 비효과적인 프롬프트 / 低效的指令

| Bad Prompt / 나쁜 프롬프트 / 差的指令 | Problem / 문제 / 问题 |
|---|---|
| "Optimize my code" / "코드 최적화해" / "帮我优化一下代码" | Too vague — performance? readability? security? / 너무 모호 — 성능? 가독성? 보안? / 太模糊——性能？可读性？安全性？ |
| Just saying "continue" without reading / 읽지 않고 "계속" / 不看输出直接说"继续" | AI may drift. Review and correct direction. / AI가 방향을 벗어날 수 있음. 검토 후 방향 수정. / AI 可能走偏，要及时纠正。 |
| Too many requests at once / 한 번에 너무 많은 요청 / 一次提太多需求 | One feature at a time, confirm OK, then next. / 한 번에 하나씩, 확인 후 다음. / 一次一个，确认再下一个。 |

### 🔑 Core Principles / 핵심 원칙 / 核心原则

1. **Describe "what", not "how"** / **"무엇을"을 설명하고 "어떻게"는 AI에게** / **描述"要什么"，不用说"怎么做"** — AI knows implementation better than you. / AI가 구현 세부사항을 더 잘 앎. / AI 比你更懂实现细节。

2. **Paste full error messages** / **전체 에러 메시지 붙여넣기** / **贴完整错误信息** — AI diagnoses from error text. / AI는 에러 텍스트로 진단. / AI 靠错误信息定位问题。

3. **Set preferences and let AI remember** / **선호도를 설정하고 AI가 기억하게** / **设置偏好让 AI 记住** — "Never restart without permission", "Docs must be bilingual" → AI follows forever. / "허락 없이 재시작 금지", "문서는 이중 언어" → AI가 계속 준수. / "不要随便重启""文档要双语" → AI 一直遵守。

4. **Let AI run commands** / **AI가 명령 실행하게** / **让 AI 跑命令** — It can operate your terminal directly. Faster than copy-paste. / 터미널을 직접 조작 가능. 복사-붙여넣기보다 빠름. / 它能直接操作终端，比你更快。

5. **Point out mistakes immediately** / **실수를 즉시 지적** / **发现错误直接指出** — "Your pushes all failed" → AI immediately checks logs and fixes. / "푸시가 전부 실패했어" → AI가 즉시 로그 확인 후 수정. / "你的推送全部失败" → AI 立刻查日志修复。

---

## 5. What AI Couldn't Do / AI가 못한 것 / AI 搞不定的事

| Task / 작업 / 任务 | Why / 이유 / 原因 |
|---|---|
| **Browser authorization** / **브라우저 인증** / **浏览器授权** | `gh auth login` requires human to click Authorize in browser / `gh auth login`은 브라우저에서 사람이 Authorize 클릭 필요 / 需要人在浏览器里点 Authorize |
| **Create GitHub repos** / **GitHub 저장소 생성** / **创建 GitHub 仓库** | Needed human to go to github.com/new (later found gh CLI can do it) / github.com/new에서 사람이 생성 필요 (나중에 gh CLI로 가능 발견) / 需要人去创建（后来发现 gh CLI 可以） |
| **Azure Portal operations** / **Azure Portal 작업** / **Azure Portal 操作** | Creating resource groups, VNets, databases / 리소스 그룹, VNet, 데이터베이스 생성 / 创建资源组、VNet、数据库 |
| **Product direction** / **제품 방향** / **判断产品方向** | AI doesn't know if you want Korean or Japanese practice / AI는 한국어 연습인지 일본어 연습인지 모름 / AI 不知道你想做韩语还是日语 |
| **Aesthetic judgment** / **미적 판단** / **审美判断** | "Does gold + navy look good?" — AI can only suggest / "골드+네이비 예뻐?" — AI는 제안만 가능 / AI 只能给建议 |
| **Corporate policy issues** / **기업 정책 문제** / **企业策略问题** | Azure AD policy blocked SP credentials — AI didn't predict this / Azure AD 정책이 SP 자격 증명 차단 — AI도 예측 못함 / 公司策略阻止 SP 凭证，AI 也没预料到 |

---

## 6. Key Lessons / 핵심 교훈 / 关键经验总结

### About AI-Assisted Development / AI 지원 개발에 대해 / 关于 AI 辅助开发

1. **AI is a 10x accelerator, not a replacement** / **AI는 10배 가속기이지 대체물이 아님** / **AI 是 10x 加速器，不是替代品**
   - EN: You still need to understand architecture, make decisions, accept/reject results.
   - KR: 여전히 아키텍처를 이해하고, 결정을 내리고, 결과를 수락/거부해야 함.
   - CN: 你仍然需要理解架构、做决策、验收结果。

2. **AI excels at implementation, not design** / **AI는 구현에 뛰어나지, 설계가 아님** / **AI 最擅长实现，而不是设计**
   - EN: Tell it "what to build", not "how to code it".
   - KR: "무엇을 만들지" 말하고, "어떻게 코딩할지"는 맡기기.
   - CN: 告诉它"做什么"比"怎么做"重要。

3. **AI makes mistakes — that's normal** / **AI는 실수함 — 정상임** / **AI 犯错很正常**
   - EN: CI/CD failed 3 times, deploy command was wrong once. Key: detect and correct fast.
   - KR: CI/CD 3번 실패, 배포 명령 1번 오류. 핵심: 빠르게 발견하고 수정.
   - CN: CI/CD 连错 3 次，部署命令用错 1 次。关键是快速发现并纠正。

4. **Let AI remember preferences** / **AI에게 선호도를 기억시키기** / **让 AI 记住偏好**
   - EN: "Never restart without permission", "Docs must be bilingual" — set once, followed forever.
   - KR: "허락 없이 재시작 금지", "문서는 이중 언어" — 한 번 설정, 영구 준수.
   - CN: "不要随便重启"、"文档要双语" — 设置一次，后面全部自动遵守。

5. **AI can operate your computer directly** / **AI는 컴퓨터를 직접 조작 가능** / **AI 能直接操作你的电脑**
   - EN: Run terminal commands, edit files, create directories. Don't copy-paste yourself.
   - KR: 터미널 명령 실행, 파일 편집, 디렉토리 생성. 직접 복사-붙여넣기 하지 말기.
   - CN: 跑终端命令、编辑文件、创建目录，不要自己复制粘贴。

### About Azure Deployment / Azure 배포에 대해 / 关于 Azure 部署

6. **Deploy method matters** / **배포 방식이 중요** / **部署方式很重要**
   - `config-zip` ≠ `deploy --type zip` — wrong one = 503

7. **URL-encode special chars in passwords** / **비밀번호 특수문자 URL 인코딩** / **密码特殊字符要编码**
   - `!` → `%21`, `@` → `%40`, `#` → `%23`

8. **Never pip install in startup.sh** / **startup.sh에서 pip install 금지** / **不要在 startup.sh 里 pip install**
   - Use Oryx build (`SCM_DO_BUILD_DURING_DEPLOYMENT=true`) — installs once, not every restart.
   - Oryx 빌드 사용 — 매 재시작이 아닌 한 번만 설치.
   - 用 Oryx build — 只装一次，不是每次重启都装。

9. **OIDC > Service Principal secrets** / **OIDC > 서비스 주체 시크릿** / **OIDC 比 SP secret 更安全**
   - No long-lived password leak risk. / 장기 비밀번호 유출 위험 없음. / 没有长期密码泄露风险。

### About Project Management / 프로젝트 관리에 대해 / 关于项目管理

10. **Separate code from secrets** / **코드와 시크릿 분리** / **代码和密码必须分离**
    - `.env` always gitignored. Secrets in GitHub Secrets / Azure App Settings.
    - `.env`는 항상 gitignore. 시크릿은 GitHub Secrets / Azure App Settings에.
    - `.env` 永远 gitignore，密码存 GitHub Secrets / Azure App Settings。

11. **Dual repo architecture** / **이중 repo 아키텍처** / **双 repo 架构**
    - Private repo auto-deploys. Public repo is showcase only. Same code.
    - 비공개 repo 자동 배포. 공개 repo는 전시용. 동일 코드.
    - 私有 repo 自动部署，公开 repo 纯展示，同一份代码。

12. **Test locally first, then push** / **먼저 로컬에서 테스트, 그 다음 푸시** / **先本地验证，再推送**
    - Never experiment on production. / 프로덕션에서 실험 금지. / 不要在生产环境上实验。

13. **Write docs while building** / **만들면서 문서 작성** / **文档要写在做的时候**
    - Retroactive docs miss details. AI writes docs fast. / 사후 문서는 세부사항 누락. AI가 빠르게 문서 작성. / 事后补文档会忘掉细节，AI 帮你写很快。

---

## 7. Tool Chain / 도구 체인 / 工具链

```
Development / 개발 / 开发:
├── VS Code + GitHub Copilot (Claude)  — Code, debug, deploy, docs / 코드, 디버그, 배포, 문서 / 写代码、调试、部署、写文档
├── Python 3.12                        — Backend language / 백엔드 언어 / 后端语言
├── FastAPI / Flask                    — Web frameworks / 웹 프레임워크 / Web 框架
├── Azure CLI (az)                     — Manage Azure resources / Azure 리소스 관리 / 管理 Azure 资源
├── GitHub CLI (gh)                    — Manage repos & secrets / 저장소 & 시크릿 관리 / 管理 repo 和 secrets
└── Git                                — Version control / 버전 관리 / 版本控制

Azure Cloud / Azure 클라우드 / Azure 云服务:
├── App Service B1 Linux               — Run applications / 애플리케이션 실행 / 运行应用
├── PostgreSQL Flexible Server         — Relational data / 관계형 데이터 / 关系数据
├── Cosmos DB NoSQL                    — Document data / 문서 데이터 / 文档数据
├── Redis Cache                        — Caching / 캐싱 / 缓存
├── AI Foundry (GPT-5-nano)            — AI conversation / AI 대화 / AI 对话
├── Speech SDK                         — STT + TTS / 음성 인식 + 합성 / 语音识别 + 合成
├── VNet + Private Endpoints           — Network security / 네트워크 보안 / 网络安全
└── Managed Identity (Entra ID)        — Passwordless auth / 비밀번호 없는 인증 / 免密认证

CI/CD:
├── GitHub Actions                     — Auto test + deploy / 자동 테스트 + 배포 / 自动测试 + 部署
├── OIDC Federated Credentials         — Passwordless Azure login / 비밀번호 없는 Azure 로그인 / 免密登录 Azure
└── Oryx Build Engine                  — Auto pip install / 자동 pip install / 自动 pip install

Methodology / 방법론 / 方法论:
└── BMAD v6.2                          — 9-agent agile dev framework / 9-에이전트 애자일 개발 프레임워크 / 9 个 AI Agent 驱动的敏捷开发框架
```

---

## Final Words / 마지막 한 마디 / 最后一句话

> EN: The entire project — from idea to production, from a single .py file to 500+ files — was built through conversation with AI in VS Code.
>
> KR: 아이디어부터 프로덕션까지, 하나의 .py 파일에서 500개 이상의 파일까지 — 전부 VS Code에서 AI와의 대화로 완성했습니다.
>
> CN: 整个项目从 idea 到生产上线、从一个 py 文件到 500+ 文件，全程在 VS Code 里跟 AI 对话完成。

> EN: AI won't make you a better programmer, but it will make you a better **product builder**.
>
> KR: AI는 더 나은 프로그래머로 만들어주지 않지만, 더 나은 **프로덕트 빌더**로 만들어줍니다.
>
> CN: AI 不会让你变成更好的程序员，但会让你成为更好的**产品构建者**。

> EN: Your value isn't in how much code you can write, but in **knowing what to build and how to verify it's right**.
>
> KR: 당신의 가치는 얼마나 많은 코드를 쓰느냐가 아니라, **무엇을 만들고 그것이 맞는지 검증하는 방법을 아는 것**입니다.
>
> CN: 你的价值不在于能写多少代码，而在于**知道要构建什么、如何验证它是对的**。
