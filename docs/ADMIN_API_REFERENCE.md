# Admin Dashboard — API Reference

# 관리자 대시보드 — API 레퍼런스

---

## Overview / 개요

This document explains how the Admin Dashboard works end-to-end: from the database (SQL), through the backend (Python/FastAPI), to the frontend (HTML/JS), and how each API endpoint is called.

이 문서는 Admin Dashboard의 전체 동작을 설명합니다: 데이터베이스(SQL)부터 백엔드(Python/FastAPI), 프론트엔드(HTML/JS)까지, 각 API 엔드포인트의 호출 방식을 포함합니다.

---

## 1. Authentication Flow / 인증 흐름

### Sequence / 시퀀스

```
Frontend                    Backend                     Config
────────                    ───────                     ──────
[Login Form]
  │ Enter admin key
  ▼
fetch('/api/admin/overview',
  headers: {X-Admin-Key: key})
                    ──▶  verify_admin()
                           │ x_admin_key == settings.JWT_SECRET ?
                           │          ──▶  .env / .env.local
                           │                JWT_SECRET=xxx
                           │
                    ◀──  403 Forbidden (mismatch)
                    ◀──  200 OK (match → return data)
  │
  ▼
sessionStorage.setItem('adminKey', key)
Show dashboard
```

### Backend — Python / 백엔드

```python
# File: app/api/admin.py

from app.core.config import get_settings
settings = get_settings()
ADMIN_SECRET = settings.JWT_SECRET          # Reuse JWT_SECRET as admin key

async def verify_admin(x_admin_key: str = Header(...)):
    """FastAPI Dependency — every admin endpoint runs this first"""
    if x_admin_key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin key")
```

### Frontend — JavaScript / 프론트엔드

```javascript
// File: static/admin_dashboard.html

// Login: validate key by calling /overview
function doLogin() {
  adminKey = document.getElementById('adminKey').value.trim();
  fetch('/api/admin/overview', { headers: { 'X-Admin-Key': adminKey } })
    .then(r => { if (!r.ok) throw new Error(); return r.json(); })
    .then(() => {
      sessionStorage.setItem('adminKey', adminKey);  // Save for session
      // Show dashboard...
    });
}

// All API calls use this helper
function api(path, opts = {}) {
  const headers = { 'X-Admin-Key': adminKey, ...opts.headers };
  if (opts.body && typeof opts.body === 'object') {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }
  return fetch(`/api/admin${path}`, { ...opts, headers })
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
}
```

---

## 2. API Endpoints / API 엔드포인트

### 2.1 GET /api/admin/overview

**Purpose / 목적**: KPI summary for dashboard cards
대시보드 카드용 KPI 요약

#### SQL Queries / SQL 쿼리

```sql
-- Total users / 전체 사용자
SELECT COUNT(id) FROM users;

-- Today signups / 오늘 가입
SELECT COUNT(id) FROM users WHERE created_at >= '2026-03-26 00:00:00+00';

-- 7-day signups / 7일 가입
SELECT COUNT(id) FROM users WHERE created_at >= NOW() - INTERVAL '7 days';

-- 30-day signups / 30일 가입
SELECT COUNT(id) FROM users WHERE created_at >= NOW() - INTERVAL '30 days';

-- DAU (today) / 일간 활성
SELECT COUNT(DISTINCT user_id) FROM study_streaks WHERE date >= '2026-03-26';

-- WAU (7 days) / 주간 활성
SELECT COUNT(DISTINCT user_id) FROM study_streaks WHERE date >= NOW() - INTERVAL '7 days';

-- MAU (30 days) / 월간 활성
SELECT COUNT(DISTINCT user_id) FROM study_streaks WHERE date >= NOW() - INTERVAL '30 days';

-- Conversations & vocab / 대화 & 단어
SELECT COUNT(id) FROM conversations;
SELECT COUNT(id) FROM vocab_book;
SELECT COUNT(id) FROM vocab_book WHERE mastered = true;
```

#### Backend — Python / 백엔드

```python
# app/api/admin.py — overview()
@router.get("/overview", dependencies=[Depends(verify_admin)])
async def overview(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    dau = (await db.execute(
        select(func.count(distinct(StudyStreak.user_id)))
        .where(StudyStreak.date >= today)
    )).scalar() or 0
    # ... (9 more queries)

    return {
        "total_users": total_users,
        "signups": {"today": ..., "week": ..., "month": ...},
        "active_users": {"dau": dau, "wau": ..., "mau": ...},
        "content": {"total_conversations": ..., "total_vocab": ..., "mastered_vocab": ...},
    }
```

#### Frontend — JavaScript / 프론트엔드

```javascript
async function loadOverview() {
  const d = await api('/overview');
  document.getElementById('kpiTotal').textContent = d.total_users;
  document.getElementById('kpiToday').textContent = d.signups.today;
  document.getElementById('kpiDAU').textContent = d.active_users.dau;
  document.getElementById('kpiConv').textContent = d.content.total_conversations;
  // ... (9 KPI cards updated)
}
```

#### Response Example / 응답 예시

```json
{
  "total_users": 25,
  "signups": {"today": 1, "week": 10, "month": 25},
  "active_users": {"dau": 0, "wau": 1, "mau": 1},
  "content": {"total_conversations": 1, "total_vocab": 0, "mastered_vocab": 0}
}
```

---

### 2.2 GET /api/admin/signups/trend

**Purpose / 목적**: Daily signup counts for chart
차트용 일간 가입 수

#### SQL / SQL 쿼리

```sql
SELECT DATE(created_at) AS date, COUNT(id) AS count
FROM users
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY DATE(created_at);
```

#### Backend / 백엔드

```python
@router.get("/signups/trend", dependencies=[Depends(verify_admin)])
async def signup_trend(days: int = 30, db: AsyncSession = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(func.date(User.created_at).label("date"), func.count(User.id).label("count"))
        .where(User.created_at >= since)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    return [{"date": str(row.date), "count": row.count} for row in result]
```

#### Frontend — Chart.js / 프론트엔드

```javascript
async function loadSignupTrend() {
  const d = await api('/signups/trend?days=30');
  makeLineChart('signupChart',
    d.map(r => r.date.slice(5)),    // labels: "03-20", "03-21"...
    d.map(r => r.count),            // data: [2, 5, 1, ...]
    '#27ae60', 'Signups'
  );
}

function makeLineChart(canvasId, labels, data, color, label) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{ label, data, borderColor: color, fill: true }] },
    options: { responsive: true, scales: { y: { beginAtZero: true } } }
  });
}
```

#### Response / 응답

```json
[
  {"date": "2026-03-20", "count": 3},
  {"date": "2026-03-21", "count": 5},
  {"date": "2026-03-22", "count": 2}
]
```

---

### 2.3 GET /api/admin/dau/trend

**Purpose / 목적**: Daily active user counts for chart
차트용 일간 활성 사용자 수

#### SQL / SQL 쿼리

```sql
SELECT DATE(date) AS date, COUNT(DISTINCT user_id) AS count
FROM study_streaks
WHERE date >= NOW() - INTERVAL '30 days'
GROUP BY DATE(date)
ORDER BY DATE(date);
```

#### Backend → Frontend: Same pattern as signups/trend (same chart function)
백엔드 → 프론트엔드: signups/trend와 동일한 패턴

---

### 2.4 GET /api/admin/study/trend

**Purpose / 목적**: Daily total study minutes for chart
차트용 일간 총 학습 시간

#### SQL / SQL 쿼리

```sql
SELECT DATE(date) AS date, COALESCE(SUM(minutes_studied), 0) AS minutes
FROM study_streaks
WHERE date >= NOW() - INTERVAL '30 days'
GROUP BY DATE(date)
ORDER BY DATE(date);
```

---

### 2.5 GET /api/admin/levels

**Purpose / 목적**: User level distribution for bar chart
바 차트용 사용자 레벨 분포

#### SQL / SQL 쿼리

```sql
SELECT korean_level, COUNT(id) FROM users GROUP BY korean_level;
```

#### Backend / 백엔드

```python
@router.get("/levels", dependencies=[Depends(verify_admin)])
async def level_distribution(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User.korean_level, func.count(User.id)).group_by(User.korean_level)
    )
    return {str(row[0].value) if row[0] else "unknown": row[1] for row in result}
```

#### Frontend — Level Bars / 프론트엔드

```javascript
async function loadLevels() {
  const d = await api('/levels');  // {"beginner": 15, "intermediate": 8, "advanced": 2}
  const total = Object.values(d).reduce((a,b) => a+b, 0) || 1;
  // Render horizontal bars with percentage width
  [['beginner','초급'], ['intermediate','중급'], ['advanced','고급']].forEach(([key,label]) => {
    const count = d[key] || 0;
    const pct = Math.round(count / total * 100);
    // Create: <div class="level-bar"><div class="fill" style="width:${pct}%">${count}</div></div>
  });
}
```

#### Response / 응답

```json
{"beginner": 15, "intermediate": 8, "advanced": 2}
```

---

### 2.6 GET /api/admin/users

**Purpose / 목적**: Paginated & filterable user list
페이지네이션 & 필터링 사용자 목록

#### Params / 파라미터

| Param | Type | Default | Description / 설명 |
|---|---|---|---|
| `page` | int | 1 | Page number / 페이지 번호 |
| `size` | int | 50 | Page size / 페이지 크기 |
| `search` | string | null | Search email/nickname via ILIKE / 이메일/닉네임 검색 |
| `level` | string | null | Filter by level (beginner/intermediate/advanced) / 레벨 필터 |
| `active` | bool | null | Filter by status / 상태 필터 |

#### SQL / SQL 쿼리

```sql
-- With search + level + active filters
SELECT id, email, nickname, korean_level, created_at, is_active
FROM users
WHERE (email ILIKE '%search%' OR nickname ILIKE '%search%')
  AND korean_level = 'beginner'
  AND is_active = true
ORDER BY created_at DESC
OFFSET 0 LIMIT 50;

-- Count for pagination
SELECT COUNT(id) FROM users WHERE ...same filters...;
```

#### Backend / 백엔드

```python
@router.get("/users", dependencies=[Depends(verify_admin)])
async def user_list(page: int = 1, size: int = 50,
                    search: Optional[str] = None,
                    level: Optional[str] = None,
                    active: Optional[bool] = None,
                    db: AsyncSession = Depends(get_db)):
    filters = []
    if search:
        like_pat = f"%{search}%"
        filters.append(or_(User.email.ilike(like_pat), User.nickname.ilike(like_pat)))
    if level:
        filters.append(User.korean_level == KoreanLevel(level))
    if active is not None:
        filters.append(User.is_active == active)

    total = (await db.execute(select(func.count(User.id)).where(and_(*filters)))).scalar()
    users = (await db.execute(
        select(User).where(and_(*filters)).order_by(User.created_at.desc())
        .offset((page-1)*size).limit(size)
    )).scalars().all()

    return {"total": total, "page": page, "size": size, "users": [...]}
```

#### Frontend — Table + Search / 프론트엔드

```javascript
// Debounced search (350ms delay)
function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadUsers(1), 350);
}

async function loadUsers(page) {
  const search = document.getElementById('userSearch').value.trim();
  const level = document.getElementById('levelFilter').value;
  const active = document.getElementById('activeFilter').value;

  let qs = `?page=${page}&size=20`;
  if (search) qs += `&search=${encodeURIComponent(search)}`;
  if (level)  qs += `&level=${level}`;
  if (active) qs += `&active=${active}`;

  const d = await api(`/users${qs}`);
  // Render <table> rows with d.users
  // Render pagination buttons with Math.ceil(d.total / d.size)
}
```

---

### 2.7 GET /api/admin/users/{user_id}

**Purpose / 목적**: User detail + study stats (shown in modal)
사용자 상세 + 학습 통계 (모달에 표시)

#### SQL / SQL 쿼리

```sql
-- User info
SELECT * FROM users WHERE id = 1;

-- Stats
SELECT COUNT(id) FROM conversations WHERE user_id = 1;
SELECT COUNT(id) FROM vocab_book WHERE user_id = 1;
SELECT COALESCE(SUM(minutes_studied), 0) FROM study_streaks WHERE user_id = 1;
SELECT COUNT(id) FROM study_streaks WHERE user_id = 1;
SELECT MAX(date) FROM study_streaks WHERE user_id = 1;
```

#### Frontend — Modal / 프론트엔드

```javascript
async function showUser(id) {
  const d = await api(`/users/${id}`);
  // Populate modal with: email, level, status, conversations, vocab, minutes, days, last_active
  openModal('userModal');
}
```

---

### 2.8 PATCH /api/admin/users/{user_id}

**Purpose / 목적**: Edit user nickname & level
사용자 닉네임 & 레벨 수정

#### SQL / SQL 쿼리

```sql
UPDATE users SET nickname = 'New Name', korean_level = 'intermediate' WHERE id = 1;
```

#### Frontend / 프론트엔드

```javascript
async function submitEdit() {
  const id = document.getElementById('editUserId').value;
  const nickname = document.getElementById('editNickname').value.trim();
  const korean_level = document.getElementById('editLevel').value;

  await api(`/users/${id}`, {
    method: 'PATCH',
    body: { nickname, korean_level }   // JSON body
  });
  toast('사용자 정보 업데이트 완료 User updated');
  loadUsers(currentPage);  // Refresh table
}
```

---

### 2.9 PATCH /api/admin/users/{user_id}/toggle

**Purpose / 목적**: Toggle user active/inactive
사용자 활성/비활성 토글

#### SQL / SQL 쿼리

```sql
-- Read current state, then flip
UPDATE users SET is_active = NOT is_active WHERE id = 1;
```

#### Frontend / 프론트엔드

```javascript
function confirmToggle(id, isActive) {
  // Show confirm modal
  document.getElementById('confirmBtn').onclick = async () => {
    await api(`/users/${id}/toggle`, { method: 'PATCH' });
    toast(`사용자 ${isActive ? '비활성화' : '활성화'} 완료`);
    loadUsers(currentPage);
  };
  openModal('confirmModal');
}
```

---

### 2.10 DELETE /api/admin/users/{user_id}

**Purpose / 목적**: Soft-delete user (set is_active=false)
소프트 삭제 (is_active=false 설정)

#### SQL / SQL 쿼리

```sql
UPDATE users SET is_active = false WHERE id = 1;
-- NOTE: Not a real DELETE — data is preserved
```

---

### 2.11 GET /api/admin/export/users

**Purpose / 목적**: Export all users as JSON (frontend converts to CSV)
전체 사용자 JSON 내보내기 (프론트엔드에서 CSV 변환)

#### SQL / SQL 쿼리

```sql
SELECT id, email, nickname, korean_level, daily_goal_minutes, created_at, is_active
FROM users ORDER BY created_at DESC;
```

#### Frontend — CSV Download / 프론트엔드

```javascript
async function exportUsers() {
  const data = await api('/export/users');   // JSON array
  const headers = ['ID', 'Email', 'Nickname', 'Level', 'Daily Goal', 'Signup', 'Active'];
  const rows = data.map(u => [u.id, u.email, u.nickname, u.level, ...]);

  // Generate CSV with BOM for Excel compatibility
  const BOM = '\uFEFF';
  const csv = BOM + [headers.join(','), ...rows.map(r =>
    r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')
  )].join('\n');

  // Download as file
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `kbcoach-users-${today()}.csv`; a.click();
}
```

---

### 2.12 GET /api/admin/export/overview

**Purpose / 목적**: Export KPI metrics as JSON (frontend converts to CSV)
KPI 지표 JSON 내보내기 (프론트엔드에서 CSV 변환)

#### Response / 응답

```json
[
  {"metric": "Total Users / 전체 사용자", "value": 25},
  {"metric": "Today Signups / 오늘 가입", "value": 1},
  {"metric": "DAU / 일간 활성", "value": 0},
  {"metric": "WAU / 주간 활성", "value": 1},
  {"metric": "MAU / 월간 활성", "value": 1},
  {"metric": "Total Conversations / 전체 대화", "value": 1},
  {"metric": "Total Vocab / 전체 단어", "value": 0},
  {"metric": "Export Date / 내보내기 날짜", "value": "2026-03-26T..."}
]
```

---

## 3. Database Schema / 데이터베이스 스키마

### Tables Used / 사용 테이블

```sql
-- users (사용자)
CREATE TABLE users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    nickname    VARCHAR(100) DEFAULT '',
    korean_level ENUM('beginner','intermediate','advanced') DEFAULT 'beginner',
    daily_goal_minutes INTEGER DEFAULT 15,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active   BOOLEAN DEFAULT TRUE
);

-- study_streaks (학습 기록 — DAU/WAU/MAU 계산용)
CREATE TABLE study_streaks (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    date            TIMESTAMP WITH TIME ZONE,
    minutes_studied INTEGER DEFAULT 0,
    UNIQUE(user_id, date)
);

-- vocab_book (단어장)
CREATE TABLE vocab_book (
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER REFERENCES users(id),
    word_ko   VARCHAR(200),
    meaning_zh VARCHAR(200),
    tags      JSONB DEFAULT '[]',
    mastered  BOOLEAN DEFAULT FALSE
);

-- conversations (대화 기록)
CREATE TABLE conversations (
    id        SERIAL PRIMARY KEY,
    user_id   INTEGER REFERENCES users(id),
    thread_id VARCHAR(255),
    title     VARCHAR(500),
    messages  JSONB DEFAULT '[]'
);
```

### SQLAlchemy ORM Mapping / SQLAlchemy ORM 매핑

```
SQL Table         →  Python Model     →  Admin API Field
─────────────────────────────────────────────────────────
users.id          →  User.id          →  response["id"]
users.email       →  User.email       →  response["email"]
users.korean_level→  User.korean_level→  response["level"]  (via .value)
users.created_at  →  User.created_at  →  response["created_at"]  (via .isoformat())
users.is_active   →  User.is_active   →  response["is_active"]
```

---

## 4. Request Flow Diagram / 요청 흐름 다이어그램

### Example: User clicks "Dashboard" tab / 사용자가 "Dashboard" 탭 클릭

```
① Browser: navigateTo('page-dashboard')
   │
② JS: loadPageData('page-dashboard')
   │
③ JS: Promise.all([
   │     loadOverview(),      → GET /api/admin/overview
   │     loadSignupTrend(),   → GET /api/admin/signups/trend?days=30
   │     loadDAUTrend(),      → GET /api/admin/dau/trend?days=30
   │     loadStudyTrend(),    → GET /api/admin/study/trend?days=30
   │     loadLevels()         → GET /api/admin/levels
   │   ])
   │
④ FastAPI: verify_admin(X-Admin-Key) → OK
   │
⑤ FastAPI: db = await get_db()
   │        → async_session() → AsyncSession (SQLAlchemy 2.0)
   │
⑥ SQLAlchemy: await db.execute(select(...))
   │           → asyncpg driver → PostgreSQL (production)
   │           → aiosqlite driver → SQLite (local dev)
   │
⑦ FastAPI: return JSON response
   │
⑧ JS: Update DOM (KPI cards, Chart.js charts, level bars)
```

### Example: Admin edits a user / 관리자가 사용자 편집

```
① Click "편집" button → openEdit(id, nickname, level)
   │
② Fill edit modal → click "저장 Save"
   │
③ JS: api(`/users/${id}`, { method: 'PATCH', body: {nickname, korean_level} })
   │
④ HTTP: PATCH /api/admin/users/5
   │     Headers: X-Admin-Key: xxx, Content-Type: application/json
   │     Body: {"nickname": "New Name", "korean_level": "intermediate"}
   │
⑤ FastAPI: verify_admin() → OK
   │        update_user(user_id=5, nickname="New Name", korean_level="intermediate")
   │
⑥ SQLAlchemy: user.nickname = "New Name"
   │            user.korean_level = KoreanLevel.INTERMEDIATE
   │            await db.commit()
   │
⑦ Response: {"id": 5, "nickname": "New Name", "level": "intermediate"}
   │
⑧ JS: closeModal() → toast('업데이트 완료') → loadUsers(currentPage)
```

---

## 5. File Map / 파일 맵

```
app/
├── api/
│   └── admin.py              ← 12 API endpoints (all admin logic)
├── core/
│   ├── config.py             ← JWT_SECRET (admin key source)
│   └── database.py           ← engine, async_session, get_db()
├── models/
│   └── models.py             ← User, StudyStreak, VocabBook, Conversation
└── main.py                   ← app.include_router(admin.router)

static/
└── admin_dashboard.html      ← Single-file frontend (HTML + CSS + JS)

docs/
├── ADMIN_DASHBOARD.md        ← Architecture & design doc
└── ADMIN_API_REFERENCE.md    ← This file (API reference)
```

---

## 6. cURL Examples / cURL 예시

```bash
# Overview
curl -H "X-Admin-Key: YOUR_KEY" https://korean-biz-coach.azurewebsites.net/api/admin/overview

# User list with search
curl -H "X-Admin-Key: YOUR_KEY" "https://korean-biz-coach.azurewebsites.net/api/admin/users?search=gmail&level=beginner&page=1"

# Edit user
curl -X PATCH -H "X-Admin-Key: YOUR_KEY" -H "Content-Type: application/json" \
  -d '{"nickname":"NewName","korean_level":"intermediate"}' \
  https://korean-biz-coach.azurewebsites.net/api/admin/users/5

# Toggle user active status
curl -X PATCH -H "X-Admin-Key: YOUR_KEY" \
  https://korean-biz-coach.azurewebsites.net/api/admin/users/5/toggle

# Export users (JSON → frontend converts to CSV)
curl -H "X-Admin-Key: YOUR_KEY" https://korean-biz-coach.azurewebsites.net/api/admin/export/users
```
