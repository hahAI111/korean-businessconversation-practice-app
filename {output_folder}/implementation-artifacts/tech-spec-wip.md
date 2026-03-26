---
title: 'Admin Dashboard V2 Phase 1 — 用户管理 + 数据导出 + Firebase Console 布局'
slug: 'admin-dashboard-v2-p1'
created: '2026-03-26'
status: 'review'
stepsCompleted: [1, 2, 3]
tech_stack: ['Python 3.12', 'FastAPI', 'SQLAlchemy 2.0 async', 'Chart.js 4', 'Vanilla JS']
files_to_modify: ['app/api/admin.py', 'app/models/models.py', 'static/admin_dashboard.html']
code_patterns: ['async def + AsyncSession', 'dependencies=[Depends(verify_admin)]', 'plain dict responses', 'X-Admin-Key header auth']
test_patterns: ['local test with SQLite + .env.local']
---

# Tech-Spec: Admin Dashboard V2 Phase 1

**Created:** 2026-03-26

## Overview

### Problem Statement

现有 admin dashboard 只有只读数据查看功能。运营团队需要：
1. 管理用户（禁用/启用、编辑信息、删除）
2. 导出数据（CSV 格式的用户列表、统计报表）
3. 更好的导航结构（当前是单页滚动，功能增加后不可扩展）

### Solution

将 admin dashboard 重构为 Firebase Console 风格（左侧边栏导航 + 内容区分页），新增用户管理 CRUD 操作和 CSV 数据导出功能。

### Scope

**In Scope:**
- Firebase Console 风格布局重构（sidebar + content area）
- 用户管理：禁用/启用、编辑昵称和等级、删除用户
- 数据导出：用户列表 CSV、KPI 报表 CSV
- 用户搜索/筛选（按邮箱、昵称、等级）

**Out of Scope:**
- 对话管理/查看（Phase 3）
- 留存/漏斗分析（Phase 2）
- admin 角色系统升级（Phase 3）
- 移动端 admin 专用 UI

## Context for Development

### Codebase Patterns

- **路由**: `APIRouter(prefix="/api/admin")` + `dependencies=[Depends(verify_admin)]`
- **数据库**: `AsyncSession` via `Depends(get_db)`, `select()` / `func` from SQLAlchemy
- **响应**: 直接返回 dict，不用 Pydantic response model
- **前端**: 单 HTML 文件，内联 CSS/JS，`fetch()` + `X-Admin-Key` header
- **认证**: `verify_admin()` 检查 `X-Admin-Key == JWT_SECRET`

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `app/api/admin.py` | 现有 7 个 admin API 端点 |
| `app/models/models.py` | User 模型 (8 fields: id, email, hashed_password, nickname, korean_level, daily_goal_minutes, created_at, is_active) |
| `app/core/auth.py` | verify_admin, get_current_user_id |
| `app/core/database.py` | AsyncSession, get_db |
| `static/admin_dashboard.html` | 现有前端 (Chart.js + table + modal) |
| `app/main.py` | Router 注册方式 |

### Technical Decisions

1. **不新建文件** — 所有后端改动在 `app/api/admin.py`，前端在 `static/admin_dashboard.html`
2. **软删除** — 使用现有 `is_active=False` 代替物理删除，保护数据完整性
3. **CSV 导出在前端生成** — 后端返回 JSON，前端 JS 转 CSV 下载，避免服务端 IO
4. **搜索在后端** — 新增 `search` 查询参数，后端 `ILIKE` 过滤

## Implementation Plan

### Tasks

- [ ] Task 1: 后端 — 新增用户管理 API 端点
  - File: `app/api/admin.py`
  - Action: 添加 3 个新端点:
    - `PATCH /api/admin/users/{user_id}/toggle` — 切换 is_active 状态
    - `PATCH /api/admin/users/{user_id}` — 编辑 nickname + korean_level
    - `DELETE /api/admin/users/{user_id}` — 软删除（设 is_active=False）
  - Notes: 复用现有 `verify_admin` 依赖，返回 dict 格式

- [ ] Task 2: 后端 — 增强用户列表端点（搜索 + 筛选）
  - File: `app/api/admin.py`
  - Action: 修改 `GET /api/admin/users` 添加查询参数:
    - `search: str = None` — 模糊搜索 email 和 nickname（ILIKE）
    - `level: str = None` — 按 korean_level 筛选
    - `active: bool = None` — 按 is_active 筛选
  - Notes: 保持向后兼容，参数皆为可选

- [ ] Task 3: 后端 — CSV 导出端点
  - File: `app/api/admin.py`
  - Action: 添加 2 个导出端点:
    - `GET /api/admin/export/users` — 全量用户列表 JSON（前端转 CSV）
    - `GET /api/admin/export/overview` — 汇总统计 JSON
  - Notes: 返回 JSON 而非直接 CSV，前端负责格式化下载

- [ ] Task 4: 前端 — Firebase Console 布局重构
  - File: `static/admin_dashboard.html`
  - Action: 重构页面结构:
    - 增加左侧 sidebar（导航菜单: Dashboard / Users / Export）
    - 内容区变为 3 个 section（可切换显示/隐藏）
    - 保留现有 login gate 不变
    - 保留 champagne gold + deep navy 主题
  - Notes: sidebar 宽度 240px，可折叠（移动端默认收起）

- [ ] Task 5: 前端 — 用户管理界面
  - File: `static/admin_dashboard.html`
  - Action: 增强 Users section:
    - 搜索栏（input + level dropdown + active filter）
    - 用户表格增加操作列（编辑/禁用/删除 按钮）
    - 编辑 modal（修改 nickname + level）
    - 确认 modal（禁用/删除操作需二次确认）
    - 操作后自动刷新列表
  - Notes: 复用现有 modal 样式，增加 confirm dialog

- [ ] Task 6: 前端 — 数据导出界面
  - File: `static/admin_dashboard.html`
  - Action: 新增 Export section:
    - "导出用户列表" 按钮 → 调用 API → JS 生成 CSV → 触发下载
    - "导出统计报表" 按钮 → 调用 API → JS 生成 CSV → 触发下载
    - CSV 列：中英文表头
  - Notes: 使用 `Blob` + `URL.createObjectURL` + `<a>` click 触发下载

### Acceptance Criteria

- [ ] AC 1: Given 管理员已登录, When 点击用户行的"禁用"按钮并确认, Then 该用户 is_active 变为 False，表格刷新显示"停用"徽章
- [ ] AC 2: Given 管理员已登录, When 点击"编辑"打开 modal 修改昵称和等级并提交, Then 用户信息更新成功，表格刷新显示新值
- [ ] AC 3: Given 管理员已登录, When 点击"删除"并确认, Then 该用户 is_active 设为 False（软删除），表格刷新
- [ ] AC 4: Given 管理员已登录, When 在搜索栏输入邮箱片段, Then 用户列表实时过滤显示匹配结果
- [ ] AC 5: Given 管理员已登录, When 选择等级筛选"intermediate", Then 仅显示中级用户
- [ ] AC 6: Given 管理员已登录, When 点击"导出用户列表", Then 浏览器下载 CSV 文件包含所有用户数据
- [ ] AC 7: Given 管理员已登录, When 点击"导出统计报表", Then 浏览器下载 CSV 文件包含 KPI 汇总
- [ ] AC 8: Given 页面加载, When dashboard 显示, Then 左侧有 Firebase Console 风格的 sidebar 导航
- [ ] AC 9: Given sidebar 导航, When 点击不同菜单项, Then 内容区切换到对应 section（Dashboard / Users / Export）

## Additional Context

### Dependencies

- 无新依赖，全部使用现有库（FastAPI, SQLAlchemy, Chart.js）

### Testing Strategy

- 本地测试：`.env.local` + SQLite + 手动操作验证
- 后端：用 curl/httpie 测试每个新 API 端点
- 前端：浏览器手动测试（CRUD 操作、CSV 下载、sidebar 导航）
- 回归：确认现有 overview/trend/users 端点和图表不受影响

### Notes

- **风险**: `DELETE` 端点用软删除而非物理删除，避免外键约束问题（Conversation/VocabBook 关联 user_id）
- **未来扩展**: Phase 2 将在 sidebar 增加 "Analytics" 菜单项，Phase 3 增加 "Conversations" 和 "Settings"
- **数据安全**: CSV 导出不包含 hashed_password 字段
