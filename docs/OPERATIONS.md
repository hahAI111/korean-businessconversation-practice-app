# 🚀 Operations & Deployment Guide / 운영 & 배포 가이드 / 运维 & 部署指南

> How to start, stop, and deploy the app. Where it runs. Showcase repo vs production repo explained.
>
> 앱을 시작, 중지, 배포하는 방법. 어디서 실행되는지. 전시용 repo와 프로덕션 repo의 차이.
>
> 如何启动、停止、部署应用。程序跑在哪里。展示 repo 和生产 repo 的区别。

---

## Table of Contents / 목차 / 目录

1. [Start & Stop the App / 앱 시작 & 중지 / 启动 & 停止](#1-start--stop-the-app--앱-시작--중지--启动--停止)
2. [Where Does It Run? / 어디서 실행되나요? / 程序跑在哪里？](#2-where-does-it-run--어디서-실행되나요--程序跑在哪里)
3. [Showcase vs Production Repo / 전시용 vs 프로덕션 Repo / 展示 vs 生产 Repo](#3-showcase-vs-production-repo--전시용-vs-프로덕션-repo--展示-vs-生产-repo)
4. [Why One Can Deploy and the Other Can't / 왜 하나는 배포되고 하나는 안 되나요 / 为什么一个能部署一个不行](#4-why-one-can-deploy-and-the-other-cant--왜-하나는-배포되고-하나는-안-되나요--为什么一个能部署一个不行)
5. [Production Repo Setup / 프로덕션 Repo 설정 / 生产 Repo 设置](#5-production-repo-setup--프로덕션-repo-설정--生产-repo-设置)

---

## 1. Start & Stop the App / 앱 시작 & 중지 / 启动 & 停止

### Local Development / 로컬 개발 / 本地开发

```bash
# Start / 시작 / 启动
cd korean-biz-agent
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Stop / 중지 / 停止
Ctrl+C

# Open browser / 브라우저 열기 / 打开浏览器
# → http://127.0.0.1:8000
```

**Prerequisites / 사전 요구사항 / 前提条件**:
- Python 3.12+ installed / 설치됨 / 已安装
- Virtual environment activated / 가상환경 활성화 / 虚拟环境已激活
- `pip install -r requirements.txt` completed / 완료 / 已完成
- `az login` for Azure AI auth / Azure AI 인증용 / Azure AI 认证用

### Azure Production / Azure 프로덕션 / Azure 生产环境

```bash
# Check status / 상태 확인 / 查看状态
az webapp show -g myappservices -n korean-biz-coach --query state -o tsv
# → "Running" or "Stopped"

# Stop the app / 앱 중지 / 停止应用
az webapp stop -g myappservices -n korean-biz-coach

# Start the app / 앱 시작 / 启动应用
az webapp start -g myappservices -n korean-biz-coach

# Restart the app / 앱 재시작 / 重启应用
az webapp restart -g myappservices -n korean-biz-coach

# View live logs / 실시간 로그 / 查看实时日志
az webapp log tail -g myappservices -n korean-biz-coach
```

### Deploy New Code / 새 코드 배포 / 部署新代码

```bash
# 1. Build zip (excludes .env, __pycache__, .git, etc.)
#    zip 빌드 (.env, __pycache__, .git 등 제외)
#    构建 zip（排除 .env、__pycache__、.git 等）
python make_zip.py

# 2. Deploy to Azure / Azure에 배포 / 部署到 Azure
#    ⚠️ MUST use config-zip, NOT "az webapp deploy --type zip"
#    ⚠️ 반드시 config-zip 사용, "az webapp deploy --type zip" 사용 금지
#    ⚠️ 必须用 config-zip，不能用 "az webapp deploy --type zip"
az webapp deployment source config-zip \
  --resource-group myappservices \
  --name korean-biz-coach \
  --src deploy.zip

# 3. Check deployment / 배포 확인 / 确认部署
az webapp show -g myappservices -n korean-biz-coach --query state -o tsv
```

> **⚠️ Important / 중요 / 重要**: `config-zip` triggers Oryx build (pip install → antenv). `az webapp deploy --type zip` does NOT trigger Oryx → results in "No module named uvicorn" → 503 error.
>
> `config-zip`은 Oryx 빌드를 트리거합니다 (pip install → antenv). `az webapp deploy --type zip`은 Oryx를 트리거하지 않아 → "No module named uvicorn" → 503 오류가 발생합니다.
>
> `config-zip` 会触发 Oryx 构建（pip install → antenv）。`az webapp deploy --type zip` 不会触发 Oryx → 导致 "No module named uvicorn" → 503 错误。

---

## 2. Where Does It Run? / 어디서 실행되나요? / 程序跑在哪里？

```
┌────────────────────────────────────────────────────────────┐
│  Azure App Service                                          │
│  Azure 앱 서비스                                            │
│  Azure 应用服务                                              │
│                                                              │
│  URL:      https://korean-biz-coach.azurewebsites.net       │
│  Region:   Canada Central / 캐나다 중부 / 加拿大中部          │
│  SKU:      B1 Linux (Python 3.12)                            │
│  Workers:  2 (uvicorn)                                       │
│  VNet:     vnet-zqopjmgp (private network / 사설 네트워크)    │
│  Auth:     Managed Identity (keyless / 키 없음 / 无密钥)     │
│                                                              │
│  Container internal paths / 컨테이너 내부 경로 / 容器内部路径: │
│  ├── /home/site/wwwroot/          ← App code / 앱 코드       │
│  ├── /home/site/wwwroot/antenv/   ← Python venv / 가상환경   │
│  └── /home/site/wwwroot/startup.sh ← Startup script / 시작   │
│                                                               │
│  Startup flow / 시작 흐름 / 启动流程:                         │
│  1. Oryx extracts build output / Oryx 빌드 출력 추출          │
│  2. Activate antenv virtual environment / antenv 활성화       │
│  3. uvicorn app.main:app --workers 2 --port 8000              │
│  4. Ready in ~4 minutes / 약 4분 후 준비 완료 / 约4分钟就绪   │
└───────────────────────────────────────────────────────────────┘

Connected services / 연결된 서비스 / 连接的服务:

  ┌──────────────────┐   ┌──────────────────┐
  │ Azure AI Foundry │   │ Azure Speech     │
  │ (GPT Agent)      │   │ (STT/TTS)        │
  │ East US 2        │   │ East US 2        │
  │ Managed Identity │   │ Managed Identity │
  └──────────────────┘   └──────────────────┘

  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │ PostgreSQL       │   │ Redis            │   │ Cosmos DB        │
  │ VNet private EP  │   │ VNet private EP  │   │ Entra ID auth    │
  │ Canada Central   │   │ Canada Central   │   │ Canada Central   │
  └──────────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 3. Showcase vs Production Repo / 전시용 vs 프로덕션 Repo / 展示 vs 生产 Repo

| Aspect / 측면 / 方面 | **Showcase Repo (Public)** / 전시용 (공개) / 展示用 (公开) | **Production Repo (Private)** / 프로덕션 (비공개) / 生产用 (私有) |
|---|---|---|
| **Visibility / 가시성 / 可见性** | Public — anyone can see / 누구나 볼 수 있음 / 任何人可见 | Private — team only / 팀만 접근 / 仅团队可见 |
| **Purpose / 목적 / 用途** | Portfolio showcase, interviews / 포트폴리오, 면접 / 作品展示、面试 | Active development, CI/CD / 활발한 개발,  CI/CD / 积极开发、CI/CD |
| **Secrets / 시크릿 / 密钥** | ❌ All replaced with placeholders / 모두 플레이스홀더로 교체 / 全部替换为占位符 | ✅ Stored in GitHub Secrets / GitHub Secrets에 저장 / 存储在 GitHub Secrets |
| **Branches / 브랜치 / 分支** | `main` only / `main`만 / 仅 `main` | `main` + `dev` + feature branches / 기능 브랜치 / 功能分支 |
| **CI/CD** | ❌ None / 없음 / 无 | ✅ GitHub Actions → auto deploy / 자동 배포 / 自动部署 |
| **Can deploy? / 배포 가능? / 能部署?** | ❌ No (no secrets) / 불가 (시크릿 없음) / 不行（无密钥） | ✅ Yes (PR merge → auto deploy) / 가능 (PR 병합 → 자동 배포) / 可以（PR合并→自动部署） |
| **PR Review** | Not needed / 불필요 / 不需要 | Required / 필수 / 必须 | 
| **Issues** | Not used / 미사용 / 不使用 | Track bugs & features / 버그 & 기능 추적 / 跟踪 bug 和功能 |
| **.env file** | Not committed / 커밋 안 됨 / 不提交 | Not committed (use GitHub Secrets) / 미커밋 (GitHub Secrets 사용) / 不提交（用 GitHub Secrets） |

---

## 4. Why One Can Deploy and the Other Can't / 왜 하나는 배포되고 하나는 안 되나요 / 为什么一个能部署一个不行

### Showcase Repo = Code Only, No Connection / 코드만, 연결 없음 / 仅代码，无连接

```
┌──────────────┐          ╳          ┌──────────────┐
│  GitHub      │ ─────────╳─────────►│  Azure       │
│  Public Repo │          ╳          │  App Service │
│  공개 Repo   │    No connection    │              │
│  公开 Repo   │    연결 없음         │  korean-biz  │
│              │    无连接            │  -coach      │
│  ❌ No secrets│                     │              │
│  ❌ No CI/CD  │                     │              │
└──────────────┘                     └──────────────┘

Anyone can clone, read code, learn — but CANNOT deploy.
누구나 clone하고, 코드를 읽고, 배울 수 있지만 — 배포는 불가능합니다.
任何人都可以 clone、阅读代码、学习 — 但无法部署。
```

### Production Repo = Code + Secrets + CI/CD Pipeline / 코드 + 시크릿 + CI/CD / 代码 + 密钥 + CI/CD

```
┌──────────────┐  PR merge   ┌──────────────┐  Auto Deploy  ┌──────────────┐
│  GitHub      │ ───────────►│  GitHub      │ ─────────────►│  Azure       │
│  Private Repo│             │  Actions     │               │  App Service │
│  비공개 Repo │             │  CI/CD       │               │              │
│  私有 Repo   │             │              │               │  korean-biz  │
│              │             │  1. ✅ Test   │               │  -coach      │
│  Secrets:    │             │  2. 📦 Build  │               │              │
│  ├ DB_PASSWORD│            │  3. 🚀 Deploy │               │              │
│  ├ REDIS_KEY │             │     az webapp│               │              │
│  ├ JWT_SECRET│             │     config-  │               │              │
│  └ SUB_ID    │             │     zip      │               │              │
└──────────────┘             └──────────────┘               └──────────────┘

Team pushes code → Auto test → Auto deploy → Users see updates
팀이 코드 푸시 → 자동 테스트 → 자동 배포 → 사용자가 업데이트 확인
团队推送代码 → 自动测试 → 自动部署 → 用户看到更新
```

### The Key Difference / 핵심 차이 / 核心区别

```
What makes deployment possible? / 배포를 가능하게 하는 것은? / 什么让部署成为可能？

┌─────────────────────────────────────────────────────────┐
│                                                          │
│  1. GitHub Secrets (encrypted) / 암호화된 시크릿 / 加密密钥│
│     ├── DATABASE_URL = postgresql://user:pass@host/db    │
│     ├── REDIS_URL = rediss://:key@host:6380/0            │
│     ├── JWT_SECRET = random-string                       │
│     └── AZURE_CREDENTIALS = service principal JSON       │
│                                                          │
│  2. GitHub Actions Workflow / 워크플로우 파일 / 工作流文件  │
│     └── .github/workflows/deploy.yml                     │
│         ├── Trigger: push to main / main에 push          │
│         ├── Steps: checkout → build → test → deploy      │
│         └── Uses: az webapp deployment source config-zip  │
│                                                          │
│  3. Azure Service Principal / 서비스 주체 / 服务主体       │
│     └── Allows GitHub to authenticate with Azure         │
│         GitHub가 Azure에 인증할 수 있게 함                  │
│         允许 GitHub 向 Azure 认证                          │
│                                                          │
│  Without these 3 things = no deployment possible          │
│  이 3가지 없이 = 배포 불가능                               │
│  没有这3样东西 = 无法部署                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Production Repo Setup / 프로덕션 Repo 설정 / 生产 Repo 设置

### Branch Strategy / 브랜치 전략 / 分支策略

```
main (production / 프로덕션 / 生产)
  │
  ├── Protected: requires PR review / PR 리뷰 필수 / 需要 PR 审查
  │   보호됨: PR 리뷰 필요
  │   受保护：需要 PR 审查
  │
  ├── Auto-deploy on merge / 병합 시 자동 배포 / 合并时自动部署
  │
  └── PR merge triggers: / PR 병합 시 트리거 / PR 合并触发:
      1. Run tests / 테스트 실행 / 运行测试
      2. Build zip / zip 빌드 / 构建 zip
      3. Deploy to Azure / Azure에 배포 / 部署到 Azure

dev (development / 개발 / 开发)
  │
  ├── Daily development / 일일 개발 / 日常开发
  ├── Push freely / 자유롭게 push / 自由推送
  └── Create PR to main when ready / 준비되면 main으로 PR 생성 / 准备好后创建 PR

feature/* (feature branches / 기능 브랜치 / 功能分支)
  │
  └── One branch per feature or bug fix / 기능이나 버그 수정당 하나의 브랜치
      每个功能或修复一个分支
```

### GitHub Actions CI/CD Workflow / CI/CD 워크플로우 / CI/CD 工作流

The production repo includes `.github/workflows/deploy.yml` that automatically:
프로덕션 repo에는 자동으로 다음을 수행하는 `.github/workflows/deploy.yml`이 포함됩니다:
生产 repo 包含 `.github/workflows/deploy.yml`，自动执行:

1. **Test** — Run pytest / 테스트 실행 / 运行测试
2. **Build** — Create deployment zip / 배포 zip 생성 / 创建部署 zip
3. **Deploy** — Push to Azure App Service / Azure에 배포 / 部署到 Azure

### Required GitHub Secrets / 필요한 GitHub Secrets / 需要的 GitHub Secrets

| Secret Name | Description / 설명 / 说明 |
|---|---|
| `AZURE_CREDENTIALS` | Service principal JSON for Azure login / Azure 로그인용 서비스 주체 / Azure 登录用服务主体 |
| `DATABASE_URL` | PostgreSQL connection string / PostgreSQL 연결 문자열 / PostgreSQL 连接字符串 |
| `REDIS_URL` | Redis connection string / Redis 연결 문자열 / Redis 连接字符串 |
| `JWT_SECRET` | JWT signing secret / JWT 서명 시크릿 / JWT 签名密钥 |
| `AZURE_SPEECH_RESOURCE_ID` | Speech resource ID / 음성 리소스 ID / 语音资源 ID |

---

## Navigation / 탐색 / 导航

| Next / 다음 / 下一篇 | Document / 문서 / 文档 |
|---|---|
| Main overview / 메인 개요 / 主要概述 | → [README.md](../README.md) |
| All files explained / 모든 파일 설명 / 所有文件说明 | → [docs/CODEBASE.md](CODEBASE.md) |
| How the AI works / AI 작동 방식 / AI 如何工作 | → [docs/AI_ENGINE.md](AI_ENGINE.md) |
| Database & storage / 데이터베이스 / 数据库 | → [docs/DATABASE.md](DATABASE.md) |
| Network & auth / 네트워크 & 인증 / 网络和认证 | → [docs/NETWORK.md](NETWORK.md) |
| BMAD methodology / BMAD 방법론 / BMAD 方法论 | → [docs/BMAD.md](BMAD.md) |
