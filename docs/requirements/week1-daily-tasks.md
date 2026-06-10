# Week 1 每日任务拆分

> 项目骨架与基础设施
> 状态：Week 1 全部完成 ✅ | 前端已初始化 ✅ | Docker 已配置 ✅ | 后端骨架完成 ✅ | 数据库已建表 ✅ | CI 已配置 ✅

---

## Day 1：FastAPI 入口 + 项目目录结构 ✅

**目标**：让后端能跑起来，访问到 `http://localhost:8000/docs` 看到 Swagger 页面。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 创建 `app/main.py` — FastAPI 应用入口 | `backend/app/main.py` |
| 2 | 创建 `app/core/__init__.py` | `backend/app/core/__init__.py` |
| 3 | 创建 `app/db/__init__.py` | `backend/app/db/__init__.py` |
| 4 | 创建 `app/models/__init__.py` | `backend/app/models/__init__.py` |
| 5 | 创建 `app/schemas/__init__.py` | `backend/app/schemas/__init__.py` |
| 6 | 创建 `app/api/__init__.py` | `backend/app/api/__init__.py` |
| 7 | 创建 `app/api/v1/__init__.py` | `backend/app/api/v1/__init__.py` |
| 8 | 创建 `app/services/__init__.py` | `backend/app/services/__init__.py` |
| 9 | 创建 `app/repositories/__init__.py` | `backend/app/repositories/__init__.py` |
| 10 | 创建 `app/rag/__init__.py` | `backend/app/rag/__init__.py` |
| 11 | 创建 `app/tasks/__init__.py` | `backend/app/tasks/__init__.py` |
| 12 | 创建 `app/integrations/__init__.py` | `backend/app/integrations/__init__.py` |
| 13 | 创建 `app/utils/__init__.py` | `backend/app/utils/__init__.py` |

### 验证标准

```bash
cd backend && poetry run uvicorn app.main:app --reload
# 浏览器访问 http://localhost:8000/docs → 看到 Swagger UI
```

---

## Day 2：核心配置模块 ✅

**目标**：配置管理、日志初始化、统一异常处理、统一响应格式全部就位。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 创建 `app/core/config.py` — 读取 `.env`，管理所有配置项 | `backend/app/core/config.py` |
| 2 | 创建 `app/core/logging.py` — 结构化日志初始化 | `backend/app/core/logging.py` |
| 3 | 创建 `app/core/exceptions.py` — 自定义异常 + 全局异常处理器 | `backend/app/core/exceptions.py` |
| 4 | 创建 `app/core/security.py` — JWT 签发/解析骨架（暂不完整） | `backend/app/core/security.py` |
| 5 | 创建 `app/core/context.py` — ContextVar 请求级上下文 | `backend/app/core/context.py` |
| 6 | 在 `main.py` 中注册全局异常处理器和日志中间件 | 更新 `backend/app/main.py` |

### 验证标准

```bash
# 启动后端，访问一个不存在的路由
curl http://localhost:8000/api/v1/nonexist
# 返回统一格式：{"code": 404, "message": "Not Found", "data": null}
```

---

## Day 3：数据库连接 + ORM 基类 + Alembic 初始化 ✅

**目标**：PostgreSQL 连接正常，Alembic 迁移框架就位，ORM 基类可用。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 创建 `app/db/base.py` — DeclarativeBase + 时间戳 Mixin | `backend/app/db/base.py` |
| 2 | 创建 `app/db/session.py` — async engine + sessionmaker + get_db() | `backend/app/db/session.py` |
| 3 | 初始化 Alembic | `backend/alembic.ini` + `backend/app/db/migrations/` |
| 4 | 配置 Alembic env.py 使用项目的 Base metadata | 更新 `app/db/migrations/env.py` |
| 5 | 在 `main.py` 中注册 startup/shutdown 事件管理数据库连接 | 更新 `backend/app/main.py` |

### 验证标准

```bash
# podman compose up postgres -d  先启动数据库
cd backend && poetry run alembic upgrade head
# 数据库中能看到 alembic_version 表
```

---

## Day 4：核心模型（Part 1）— 租户 + 用户 + 知识库 + 文档 ✅

**目标**：4 张核心业务表的 ORM 模型写好，Alembic 能生成迁移脚本。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 创建 `app/models/tenant.py` — 租户表模型 | `backend/app/models/tenant.py` |
| 2 | 创建 `app/models/user.py` — 用户表模型 | `backend/app/models/user.py` |
| 3 | 创建 `app/models/knowledge_base.py` — 知识库表模型 | `backend/app/models/knowledge_base.py` |
| 4 | 创建 `app/models/document.py` — 文档表模型 | `backend/app/models/document.py` |
| 5 | 更新 `app/models/__init__.py` — 导入所有模型让 Alembic 能识别 | 更新 `backend/app/models/__init__.py` |
| 6 | 生成 Alembic 迁移脚本 | `poetry run alembic revision --autogenerate -m "add tenant user kb doc tables"` |

### 验证标准

```bash
poetry run alembic upgrade head
# PostgreSQL 中能看到 tenants、users、knowledge_bases、documents 4 张表
```

---

## Day 5：核心模型（Part 2）— 对话 + 消息 + 工单 + 审计 + Agent 执行记录 ✅

**目标**：剩余 5 张表的 ORM 模型写好，全部 9 张表在数据库中建好。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 创建 `app/models/conversation.py` — 对话表模型 | `backend/app/models/conversation.py` |
| 2 | 创建 `app/models/conversation_message.py` — 对话消息表模型 | `backend/app/models/conversation_message.py` |
| 3 | 创建 `app/models/ticket.py` — 工单表模型 | `backend/app/models/ticket.py` |
| 4 | 创建 `app/models/audit_log.py` — 审计日志表模型 | `backend/app/models/audit_log.py` |
| 5 | 创建 `app/models/agent_run.py` — Agent 执行记录表模型 | `backend/app/models/agent_run.py` |
| 6 | 更新 `app/models/__init__.py` — 补充新增模型导入 | 更新 `backend/app/models/__init__.py` |
| 7 | 生成迁移脚本 + 执行 | `poetry run alembic revision --autogenerate` + `upgrade head` |

### 验证标准

```bash
poetry run alembic upgrade head
# PostgreSQL 中能看到全部 9 张表 + 索引
```

---

## Day 6：API 路由骨架 + 依赖注入 + 初始数据脚本 ✅

**目标**：API v1 路由框架搭好，能访问 `/api/v1/` 看到路由列表，能初始化默认数据。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 创建 `app/api/v1/router.py` — 聚合路由，挂载前缀 `/api/v1` | `backend/app/api/v1/router.py` |
| 2 | 创建 `app/api/deps.py` — get_db + get_current_user 骨架 | `backend/app/api/deps.py` |
| 3 | 创建 `app/api/v1/auth.py` — 登录接口骨架（暂时 mock） | `backend/app/api/v1/auth.py` |
| 4 | 创建 `app/schemas/auth.py` — LoginRequest / TokenResponse | `backend/app/schemas/auth.py` |
| 5 | 创建 `app/db/init_db.py` — 创建默认租户 + 管理员账号 | `backend/app/db/init_db.py` |
| 6 | 创建 `scripts/init_demo_data.py` — 导入示例测试数据 | `scripts/init_demo_data.py` |

### 验证标准

```bash
# 访问 http://localhost:8000/docs → 能看到所有注册的路由
# 运行 init_db → 数据库中出现默认租户和管理员账号
curl -X POST http://localhost:8000/api/v1/auth/login -d '{"email":"admin@acme.com","password":"123456"}'
# 返回 mock 的 token（JWT 完整实现留到 Week 2）
```

---

## Day 7：集成验证 + CI 跑通 + Podman Compose 全栈启动 ✅

**目标**：全部服务能通过 Podman Compose 一键启动，CI Backend 流水线跑通。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 验证后端本地启动 + 数据库连接 + API 访问 | 手动验证 |
| 2 | 验证 `podman compose up -d` 全栈能跑 | 手动验证 |
| 3 | 运行 `poetry run ruff check` + `poetry run black --check` 确保 lint 通过 | 手动验证 |
| 4 | 修复 CI 可能报的问题（lint / import 顺序等） | 按需修复 |
| 5 | push 到 GitHub，确认 CI Backend workflow 通过 | 手动验证 |
| 6 | 更新 `PROGRESS.md` 记录 Week 1 完成状态 | 更新 `PROGRESS.md` |
| 7 | 更新 `README.md` 补充后端启动说明 | 更新 `README.md` |

### 验证标准

```bash
# 全栈启动
podman compose up -d
# 后端 API 可访问
curl http://localhost:8000/docs
# 前端页面可访问
curl http://localhost:3000
# PostgreSQL 有 9 张表 + 默认数据
podman compose exec postgres psql -U supportforge -c "\dt"
# GitHub Actions CI Backend ✅ 通过
```

---

## 已完成的任务（不需要再做）

以下 Week 1 任务在之前的项目配置中已经完成：

| 任务 | 产出文件 | 状态 |
|------|----------|------|
| 初始化前端 Next.js + TS + Tailwind + shadcn/ui | `frontend/` 全套 | ✅ 已完成 |
| 配置 Podman Compose | `compose.yml` | ✅ 已完成 |
| 配置 `.env` 模板 | `backend/.env.example` | ✅ 已完成 |
| 创建 Agent Prompt 文件 | `backend/app/agent/prompts/*.md` | ✅ 已完成 |
| 配置 CI/CD 流水线 | `.github/workflows/*.yml` | ✅ 已完成 |
| 创建 Dockerfile | `backend/Dockerfile` + `frontend/Dockerfile` | ✅ 已完成 |

---

## Week 1 完成后的项目状态预期

```
backend/app/
├── main.py              ✅ FastAPI 入口，Swagger 可访问
├── core/
│   ├── config.py        ✅ 配置管理
│   ├── logging.py       ✅ 统一日志
│   ├── exceptions.py    ✅ 统一异常 + 响应格式
│   ├── security.py      ✅ JWT 骨架
│   └── context.py       ✅ 请求级上下文
├── db/
│   ├── base.py          ✅ ORM 基类 + Mixin
│   ├── session.py       ✅ 数据库连接
│   ├── init_db.py       ✅ 初始化脚本
│   └── migrations/      ✅ Alembic 迁移
├── models/              ✅ 9 张表模型
├── schemas/
│   └── auth.py          ✅ 认证 Schema
├── api/
│   ├── deps.py          ✅ 依赖注入骨架
│   └── v1/
│       ├── router.py    ✅ 路由聚合
│       └── auth.py      ✅ 登录接口骨架
├── agent/prompts/       ✅ 5 个 prompt 文件（已有）
└── 其他目录 __init__.py  ✅ 空占位

PostgreSQL: 9 张表 + 索引 + 默认租户和管理员账号
Podman Compose: 全栈可一键启动
CI/CD: CI Backend workflow ✅ 通过
```