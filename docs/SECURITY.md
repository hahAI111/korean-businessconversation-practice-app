# 🔐 Secrets & Security Architecture
# 🔐 시크릿 & 보안 아키텍처
# 🔐 密钥与安全架构

> **How passwords and secrets are managed — kept safe, never exposed in code**
>
> **비밀번호와 시크릿 관리 방법 — 안전하게 보관, 코드에 절대 노출되지 않음**
>
> **密码和密钥的管理方式 — 安全保存，绝不暴露在代码中**

---

## 1. Where Are Secrets Stored? / 시크릿은 어디에 저장되나요? / 密钥存储在哪里？

| Location / 위치 / 位置 | Has Secrets? / 시크릿 유무 / 有密钥？ | Purpose / 용도 / 用途 |
|---|---|---|
| **Local `.env` file** | ✅ Yes | Real passwords for local development / 로컬 개발용 실제 비밀번호 / 本地开发用的真实密码 |
| **GitHub Public Repo** | ❌ No | All secrets replaced with placeholders / 모든 시크릿이 플레이스홀더로 대체됨 / 所有密钥已替换为占位符 |
| **GitHub Private Repo** | ❌ No | Code has no secrets; secrets live in GitHub Secrets / 코드에 시크릿 없음; GitHub Secrets에 저장 / 代码中无密钥；密钥在GitHub Secrets中 |
| **GitHub Secrets** | ✅ Yes (encrypted) | Only CI/CD can read; humans cannot view values / CI/CD만 읽기 가능; 사람은 값 확인 불가 / 仅CI/CD可读取；人无法查看值 |
| **Azure App Service** | ✅ Yes | Injected as environment variables (App Settings) / 환경 변수로 주입 (App Settings) / 通过环境变量注入（App Settings） |

### Visual Overview / 시각적 개요 / 可视化概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SECRET LOCATIONS / 密钥位置                       │
│                                                                     │
│  LOCAL (Your PC / 你的电脑)                                          │
│  ┌──────────────┐                                                   │
│  │   .env file  │◄── Real passwords here (NEVER uploaded)           │
│  │   (gitignored)│    真实密码在这里（永远不会上传）                      │
│  └──────────────┘    실제 비밀번호 여기 (절대 업로드 안 됨)              │
│                                                                     │
│  GITHUB                                                             │
│  ┌──────────────┐    ┌──────────────────┐                           │
│  │ Public Repo  │    │  Private Repo    │                           │
│  │ (showcase)   │    │  (production)    │                           │
│  │ ❌ No secrets │    │  ❌ No secrets    │                           │
│  │ 无密钥       │    │  in code 代码无密钥 │                          │
│  └──────────────┘    │  ┌────────────┐  │                           │
│                      │  │  Secrets   │  │                           │
│                      │  │  (encrypted)│  │                           │
│                      │  │  ✅ 7 keys  │  │                           │
│                      │  └────────────┘  │                           │
│                      └──────────────────┘                           │
│                                                                     │
│  AZURE CLOUD                                                        │
│  ┌──────────────────────────────┐                                   │
│  │  App Service (App Settings)  │                                   │
│  │  ✅ Environment variables     │◄── Set by CI/CD or Azure Portal  │
│  │  ✅ 환경 변수 / 环境变量       │    CI/CD 또는 Azure Portal에서 설정 │
│  └──────────────────────────────┘    由CI/CD或Azure Portal设置        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Two Layers of Protection / 두 가지 보호 계층 / 两层保护机制

### Layer 1: `.gitignore` / 레이어 1: `.gitignore` / 第一层：`.gitignore`

The `.env` file is listed in `.gitignore`, so Git **completely ignores it**. It will never be committed or pushed.

`.env` 파일은 `.gitignore`에 등록되어 있어 Git이 **완전히 무시**합니다. 커밋이나 푸시되지 않습니다.

`.env` 文件写在 `.gitignore` 中，Git **完全忽略它**。永远不会被提交或推送。

```gitignore
# .gitignore
.env
.env.local
.env.production
```

```
$ git status
  → .env does NOT appear (invisible to Git)
  → .env 파일이 표시되지 않음 (Git에게 보이지 않음)
  → .env 不会出现（对Git不可见）
```

### Layer 2: Code Cleanup / 레이어 2: 코드 정리 / 第二层：代码清理

Before pushing to GitHub, we **manually cleaned** all hardcoded secrets from source files:

GitHub에 푸시하기 전에 소스 파일에서 하드코딩된 모든 시크릿을 **수동으로 정리**했습니다:

推送到GitHub之前，我们**手动清理了**源文件中所有硬编码的密钥：

| File / 파일 / 文件 | What was removed / 제거된 내용 / 删除内容 | Replaced with / 대체된 내용 / 替换为 |
|---|---|---|
| `README.md` | 9 instances of real passwords / 실제 비밀번호 9건 / 9处真实密码 | `<YOUR_PASSWORD>`, `<YOUR_KEY>` placeholders |
| `docs/ARCHITECTURE.md` | 3 instances of connection strings / 연결 문자열 3건 / 3处连接字符串 | Generic examples |
| `app/core/config.py` | Hardcoded Azure subscription ID / 하드코딩된 구독 ID / 硬编码的订阅ID | Empty string `""` |

### `.env.example` — Safe Template / 안전한 템플릿 / 安全模板

We provide `.env.example` with **placeholder values only** so new developers know what variables are needed:

새 개발자가 필요한 변수를 알 수 있도록 **플레이스홀더 값만 있는** `.env.example`을 제공합니다:

我们提供只有**占位符值**的 `.env.example`，让新开发者知道需要哪些变量：

```env
# .env.example (SAFE — no real values / 安全 — 没有真实值)
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname?ssl=require
REDIS_URL=rediss://:your-access-key@your-host:6380/0
JWT_SECRET=your-random-secret-here
AZURE_SPEECH_RESOURCE_ID=/subscriptions/xxx/resourceGroups/xxx/...
```

---

## 3. How Each Environment Gets Secrets / 각 환경별 시크릿 획득 방법 / 各环境如何获取密钥

### Local Development / 로컬 개발 / 本地开发

```
App starts → reads .env file → gets DATABASE_URL, REDIS_URL, JWT_SECRET, etc.
앱 시작 → .env 파일 읽기 → DATABASE_URL, REDIS_URL, JWT_SECRET 등 획득
应用启动 → 读取 .env 文件 → 获取 DATABASE_URL, REDIS_URL, JWT_SECRET 等
```

The `.env` file **never leaves your computer**. It's in `.gitignore`.

`.env` 파일은 **절대로 컴퓨터 밖으로 나가지 않습니다**. `.gitignore`에 등록되어 있습니다.

`.env` 文件**永远不会离开你的电脑**。它在 `.gitignore` 中。

### Azure Production / Azure 프로덕션 / Azure 生产环境

```
App starts → reads OS environment variables → App Service "App Settings"
앱 시작 → OS 환경 변수 읽기 → App Service "App Settings"
应用启动 → 读取操作系统环境变量 → App Service "App Settings"
```

These are set in Azure Portal > App Service > Configuration > Application Settings.

Azure Portal > App Service > 구성 > 애플리케이션 설정에서 설정합니다.

在 Azure Portal > App Service > 配置 > 应用程序设置 中配置。

### CI/CD Deployment / CI/CD 배포 / CI/CD 部署

```
GitHub Actions runs → reads GitHub Secrets → deploys code + sets App Settings
GitHub Actions 실행 → GitHub Secrets 읽기 → 코드 배포 + App Settings 설정
GitHub Actions 运行 → 读取 GitHub Secrets → 部署代码 + 设置 App Settings
```

```
┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐
│   Developer     │      │  GitHub Actions  │      │  Azure App     │
│   git push      │─────►│  reads Secrets   │─────►│  Service       │
│   开发者推送代码  │      │  读取密钥         │      │  receives code │
│   개발자 코드 푸시│      │  시크릿 읽기      │      │  + App Settings│
└─────────────────┘      └──────────────────┘      └────────────────┘
                          7 Encrypted Secrets:
                          • AZURE_CLIENT_ID
                          • AZURE_TENANT_ID
                          • AZURE_SUBSCRIPTION_ID
                          • DATABASE_URL
                          • REDIS_URL
                          • JWT_SECRET
                          • AZURE_SPEECH_RESOURCE_ID
```

---

## 4. GitHub Secrets — What's Stored / GitHub Secrets — 저장된 내용 / GitHub Secrets — 存储内容

These 7 secrets are set on the **private production repo** (`korean-biz-agent-dev`):

이 7개 시크릿은 **비공개 프로덕션 저장소** (`korean-biz-agent-dev`)에 설정되어 있습니다:

这7个密钥设置在**私有生产仓库** (`korean-biz-agent-dev`) 上：

| Secret Name | Purpose / 용도 / 用途 |
|---|---|
| `AZURE_CLIENT_ID` | OIDC login — Service Principal app ID / OIDC 로그인 — 서비스 주체 앱 ID / OIDC登录 — 服务主体应用ID |
| `AZURE_TENANT_ID` | OIDC login — Azure AD tenant / OIDC 로그인 — Azure AD 테넌트 / OIDC登录 — Azure AD租户 |
| `AZURE_SUBSCRIPTION_ID` | OIDC login — Azure subscription / OIDC 로그인 — Azure 구독 / OIDC登录 — Azure订阅 |
| `DATABASE_URL` | PostgreSQL connection string / PostgreSQL 연결 문자열 / PostgreSQL连接字符串 |
| `REDIS_URL` | Redis cache connection / Redis 캐시 연결 / Redis缓存连接 |
| `JWT_SECRET` | JWT token signing key / JWT 토큰 서명 키 / JWT令牌签名密钥 |
| `AZURE_SPEECH_RESOURCE_ID` | Azure AI Speech resource / Azure AI Speech 리소스 / Azure AI语音资源 |

### OIDC vs Traditional Secrets / OIDC vs 기존 시크릿 / OIDC vs 传统密钥

We use **OIDC (OpenID Connect)** for Azure login — no long-lived passwords:

Azure 로그인에 **OIDC (OpenID Connect)**를 사용합니다 — 장기 비밀번호 없음:

我们使用 **OIDC (OpenID Connect)** 登录Azure — 无需长期密码：

```
Traditional (old) / 기존 방식 / 传统方式:
  GitHub Secret stores: { clientId, clientSecret, tenantId, subscriptionId }
                          └── This password can leak! / 이 비밀번호가 유출될 수 있음! / 这个密码可能泄露！

OIDC (our approach) / OIDC (우리 방식) / OIDC（我们的方式）:
  GitHub Actions ──► Azure AD: "Here's my GitHub identity token"
  Azure AD: "I trust GitHub. Here's a temporary access token (1 hour)"
                     └── No stored password! / 저장된 비밀번호 없음! / 无需存储密码！
```

---

## 5. What If Secrets Are Compromised? / 시크릿이 유출되면? / 密钥泄露怎么办？

| Scenario / 시나리오 / 场景 | Action / 조치 / 操作 |
|---|---|
| `.env` file leaked / `.env` 유출 / `.env` 泄露 | Rotate all passwords in Azure Portal, generate new `.env` / Azure Portal에서 모든 비밀번호 변경, 새 `.env` 생성 / 在Azure Portal轮换所有密码，生成新 `.env` |
| GitHub Secret exposed / GitHub Secret 노출 / GitHub Secret 暴露 | Delete + recreate in repo Settings → Secrets / 저장소 설정 → Secrets에서 삭제 후 재생성 / 在仓库 Settings → Secrets 中删除并重建 |
| Azure App Settings exposed / App Settings 노출 / App Settings 暴露 | Rotate DB password, Redis key, JWT secret in Azure Portal / Azure Portal에서 DB 비밀번호, Redis 키, JWT 시크릿 변경 / 在Azure Portal轮换DB密码、Redis密钥、JWT密钥 |

### Key Rotation Checklist / 키 교체 체크리스트 / 密钥轮换清单

```
1. Change password/key in Azure Portal
   Azure Portal에서 비밀번호/키 변경
   在Azure Portal中更改密码/密钥

2. Update local .env file
   로컬 .env 파일 업데이트
   更新本地 .env 文件

3. Update GitHub Secrets (gh secret set ... --repo ...)
   GitHub Secrets 업데이트
   更新GitHub Secrets

4. Update Azure App Service App Settings (or redeploy via CI/CD)
   Azure App Service App Settings 업데이트 (또는 CI/CD로 재배포)
   更新Azure App Service App Settings（或通过CI/CD重新部署）
```

---

## 6. Summary: Code ≠ Secrets / 요약: 코드 ≠ 시크릿 / 总结：代码 ≠ 密钥

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEPARATION PRINCIPLE                          │
│                    분리 원칙 / 分离原则                            │
│                                                                 │
│   CODE (public, shareable)    SECRETS (private, encrypted)      │
│   코드 (공개, 공유 가능)        시크릿 (비공개, 암호화)             │
│   代码（公开、可共享）           密钥（私密、加密）                  │
│                                                                 │
│   ├── app/                    ├── .env (local only)             │
│   ├── static/                 ├── GitHub Secrets (encrypted)    │
│   ├── tests/                  └── Azure App Settings (cloud)    │
│   ├── docs/                                                     │
│   └── .env.example ◄── Template only, no real values            │
│                        템플릿만, 실제 값 없음                     │
│                        仅模板，无真实值                           │
│                                                                 │
│   ✅ Safe to share publicly    🔒 Never in Git history           │
│   ✅ 공개 공유 안전             🔒 Git 이력에 절대 없음             │
│   ✅ 可安全公开共享             🔒 绝不在Git历史中                  │
└─────────────────────────────────────────────────────────────────┘
```
