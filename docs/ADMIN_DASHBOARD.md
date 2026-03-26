# Admin Dashboard — Architecture & Design

# 관리자 대시보드 — 아키텍처 & 설계

---

## 1. Overview / 개요

The Admin Dashboard is an internal management tool for KBCoach (Korean Business Coach). It provides real-time KPI monitoring, user management, and data export capabilities in a **Firebase Console-style** single-page application.

관리자 대시보드는 KBCoach(한국 비즈니스 코치)의 내부 관리 도구입니다. **Firebase Console 스타일**의 싱글 페이지 애플리케이션으로 실시간 KPI 모니터링, 사용자 관리, 데이터 내보내기 기능을 제공합니다.

**URL**: `/static/admin_dashboard.html`

---

## 2. Architecture / 아키텍처

```
┌────────────────────────────────────────────────────────┐
│  Browser (Frontend)                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  admin_dashboard.html                            │  │
│  │  - HTML layout (Firebase Console sidebar)        │  │
│  │  - CSS (champagne gold + deep navy theme)        │  │
│  │  - Vanilla JS (fetch API, Chart.js 4)            │  │
│  └────────────┬─────────────────────────────────────┘  │
│               │ HTTP (fetch + X-Admin-Key header)      │
└───────────────┼────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────┐
│  Backend (FastAPI)                                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  app/api/admin.py                                │  │
│  │  - 12 API endpoints (/api/admin/*)               │  │
│  │  - Admin auth: verify_admin() dependency         │  │
│  │  - SQLAlchemy 2.0 async queries                  │  │
│  └────────────┬─────────────────────────────────────┘  │
│               │                                        │
│  ┌────────────▼─────────────────────────────────────┐  │
│  │  app/core/database.py                            │  │
│  │  - create_async_engine (SQLAlchemy 2.0)          │  │
│  │  - async_sessionmaker → AsyncSession             │  │
│  └────────────┬─────────────────────────────────────┘  │
└───────────────┼────────────────────────────────────────┘
                │
┌───────────────▼────────────────────────────────────────┐
│  Database                                              │
│  - Local: SQLite (aiosqlite)                           │
│  - Production: PostgreSQL (asyncpg, Azure)             │
│  Tables: users, study_streaks, vocab_book,             │
│          conversations                                 │
└────────────────────────────────────────────────────────┘
```

---

## 3. Authentication / 인증

### How It Works / 작동 방식

The dashboard uses **API Key authentication** via the `X-Admin-Key` HTTP header.

대시보드는 `X-Admin-Key` HTTP 헤더를 통한 **API 키 인증**을 사용합니다.

```
Client → Header: X-Admin-Key: <secret> → Server
Server → verify_admin() → Compare with settings.JWT_SECRET
         Match    → 200 OK (proceed)
         Mismatch → 403 Forbidden
```

| Environment / 환경 | Key Source / 키 출처 | Value / 값 |
|---|---|---|
| Local Dev / 로컬 개발 | `.env.local` → `JWT_SECRET` | `local-dev-secret-not-for-production` |
| Production / 프로덕션 | App Service env var → `JWT_SECRET` | (set in Azure Portal) |

### Backend Logic / 백엔드 로직

```python
# app/api/admin.py
ADMIN_SECRET = settings.JWT_SECRET  # Reuse JWT_SECRET as admin key

async def verify_admin(x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin key")
```

### Frontend Logic / 프론트엔드 로직

```javascript
// Login: test the key by calling /overview
fetch('/api/admin/overview', { headers: { 'X-Admin-Key': key } })
  .then(r => { if (!r.ok) throw new Error(); /* show dashboard */ })

// All subsequent calls include the key
function api(path, opts = {}) {
  const headers = { 'X-Admin-Key': adminKey, ...opts.headers };
  return fetch(`/api/admin${path}`, { ...opts, headers });
}
```

The key is stored in `sessionStorage` (cleared when browser tab closes).

키는 `sessionStorage`에 저장됩니다 (브라우저 탭 닫으면 삭제).

---

## 4. Pages & Features / 페이지 & 기능

### 4.1 Dashboard Page / 대시보드 페이지

**Purpose / 목적**: Overview of all KPI metrics and trends.
모든 KPI 지표와 트렌드 개요.

| Component / 컴포넌트 | API Endpoint | Data / 데이터 |
|---|---|---|
| 9 KPI Cards | `GET /overview` | Total Users, Today/Week/Month Signups, DAU/WAU/MAU, Conversations, Vocab |
| Signup Trend Chart | `GET /signups/trend?days=30` | Daily signup counts (30 days) |
| DAU Trend Chart | `GET /dau/trend?days=30` | Daily active users (30 days) |
| Study Minutes Chart | `GET /study/trend?days=30` | Daily study minutes (30 days) |
| Level Distribution | `GET /levels` | Beginner / Intermediate / Advanced counts |

**Charts** use [Chart.js 4](https://www.chartjs.org/) — line charts with gradient fill.

### 4.2 Users Page / 사용자 관리 페이지

**Purpose / 목적**: Search, filter, view, edit, toggle, and delete users.
사용자 검색, 필터링, 상세 보기, 편집, 활성화/비활성화, 삭제.

| Action / 동작 | API | Method | Description / 설명 |
|---|---|---|---|
| List | `GET /users?page=&size=&search=&level=&active=` | GET | Paginated user list with filters / 필터링된 사용자 목록 |
| Detail | `GET /users/{id}` | GET | User detail + study stats / 사용자 상세 + 학습 통계 |
| Edit | `PATCH /users/{id}` | PATCH | Update nickname & level / 닉네임 & 레벨 수정 |
| Toggle | `PATCH /users/{id}/toggle` | PATCH | Flip is_active / 활성 상태 토글 |
| Delete | `DELETE /users/{id}` | DELETE | Soft-delete (set is_active=false) / 소프트 삭제 |

**Search 검색**: 350ms debounced, searches `email` and `nickname` via `ILIKE`.

### 4.3 Export Page / 데이터 내보내기 페이지

**Purpose / 목적**: Download data as CSV files.
데이터를 CSV 파일로 다운로드.

| Export / 내보내기 | API | Content / 내용 |
|---|---|---|
| User List / 사용자 목록 | `GET /export/users` | All users (ID, email, nickname, level, goal, signup, status) |
| KPI Report / KPI 보고서 | `GET /export/overview` | 10 KPI metrics summary |

CSV files include a BOM (byte order mark) for Excel Korean/UTF-8 compatibility.

CSV 파일에는 Excel 한국어/UTF-8 호환을 위한 BOM이 포함됩니다.

---

## 5. Data Flow / 데이터 흐름

### KPI Calculation Logic / KPI 계산 로직

```
Total Users = COUNT(users)
Today Signups = COUNT(users WHERE created_at >= today 00:00 UTC)
DAU = COUNT(DISTINCT study_streaks.user_id WHERE date >= today)
WAU = COUNT(DISTINCT study_streaks.user_id WHERE date >= 7 days ago)
MAU = COUNT(DISTINCT study_streaks.user_id WHERE date >= 30 days ago)
```

**Key Point / 핵심**: DAU/WAU/MAU are based on `study_streaks` table, not login records. A user is "active" only if they have a study streak entry for that day.

**핵심**: DAU/WAU/MAU는 로그인 기록이 아닌 `study_streaks` 테이블을 기반으로 합니다. 해당 날짜에 학습 기록이 있는 사용자만 "활성"으로 카운트됩니다.

### Database Tables Used / 사용되는 데이터베이스 테이블

| Table | Columns Used | Dashboard Purpose / 대시보드 용도 |
|---|---|---|
| `users` | id, email, nickname, korean_level, created_at, is_active | User list, signup trend, level distribution |
| `study_streaks` | user_id, date, minutes_studied | DAU/WAU/MAU, study trend chart |
| `vocab_book` | id, user_id, mastered | Total vocab count, mastered count |
| `conversations` | id, user_id | Total conversation count |

---

## 6. Backend Services / 백엔드 서비스

| Service / 서비스 | Technology / 기술 | Role / 역할 |
|---|---|---|
| Web Framework | **FastAPI** (Python 3.12) | API routing, dependency injection, async |
| ORM | **SQLAlchemy 2.0** (async) | Database queries with `select()`, `func.count()` |
| DB (Local) | **SQLite** + aiosqlite | Local development database |
| DB (Prod) | **Azure PostgreSQL** + asyncpg | Production database with SSL |
| Charts | **Chart.js 4** (CDN) | Frontend line charts & bar charts |
| Server | **Uvicorn** | ASGI server, serves static files via FastAPI |

---

## 7. Frontend Design / 프론트엔드 설계

### Layout / 레이아웃

Firebase Console-inspired layout:

```
┌──────────┬────────────────────────────────┐
│          │  Topbar (page title + refresh) │
│ Sidebar  ├────────────────────────────────┤
│          │                                │
│ • Dash   │  Content Area                  │
│ • Users  │  (KPIs / Tables / Charts)      │
│ • Export │                                │
│          │                                │
│──────────│                                │
│ [Logout] │                                │
└──────────┴────────────────────────────────┘
```

### Navigation / 네비게이션

```javascript
// SPA-style page switching (no router, just show/hide)
function navigateTo(pageId) {
  // 1. Update sidebar active state
  // 2. Show target page, hide others
  // 3. Load data for the page
  loadPageData(pageId);  // Triggers API calls
}
```

### Theme / 테마

- Colors: Champagne Gold (`#c9a96e`) + Deep Navy (`#0b0e13`)
- Bilingual: All text in Korean + English (한국어 + 영어)
- Responsive: Sidebar hidden on mobile (< 768px)

---

## 8. How to Use / 사용 방법

### Local Development / 로컬 개발

```bash
# 1. Start the server / 서버 시작
cd Projects/korean-biz-agent
uvicorn app.main:app --reload --port 8000

# 2. Open dashboard / 대시보드 열기
# http://127.0.0.1:8000/static/admin_dashboard.html

# 3. Enter admin key / 관리자 키 입력
# Key: value of JWT_SECRET from .env.local
```

### Production / 프로덕션

```
# URL:  https://korean-biz-coach.azurewebsites.net/static/admin_dashboard.html
# Key:  JWT_SECRET set in Azure App Service Configuration
```

### Quick Tips / 빠른 팁

- **Refresh data / 데이터 새로고침**: Click 🔄 Refresh button in topbar
- **Search users / 사용자 검색**: Type in the search box (auto-searches after 350ms)
- **Export CSV**: Go to Export page → click download button
- **View user detail / 사용자 상세**: Click the email link in user table

---

## 9. Security Considerations / 보안 고려사항

| Item / 항목 | Implementation / 구현 |
|---|---|
| Auth | API Key via `X-Admin-Key` header (not URL param) |
| Key storage | `sessionStorage` (tab-scoped, not persistent) |
| Soft delete | Users are deactivated, not permanently deleted |
| XSS protection | `escHtml()` for all user-generated content in DOM |
| CORS | FastAPI default (same-origin for static files) |
| SQL injection | SQLAlchemy parameterized queries (no raw SQL) |

### Future Improvements / 향후 개선

- [ ] Role-based admin auth (`is_admin` field on User model)
- [ ] Retention analysis (D1/D7/D30)
- [ ] Conversation management (view/search conversations)
- [ ] Audit logging for admin actions
