# SupportForge

企业级 SaaS 智能客服 AI 平台 —— 多租户隔离、RAG 知识检索、LangGraph 智能体编排、工单自动流转。

---

## 当前项目状态（Week 1 收口版）

> **重要**：本项目处于 Week 1 骨架完成阶段，以下标注各模块的真实完成状态。

### 已实现（Week 1）

- 🏢 多租户数据隔离模型（9 张核心表，tenant_id 字段强制隔离）
- 🔐 RBAC 角色定义模型（platform_admin / tenant_admin / support_agent / auditor）
- 📋 知识库 / 文档 / 对话 / 工单数据模型已建表
- 🔑 Mock 登录接口（仅支持默认管理员，JWT 认证留到 Week 2）
- 🗄️ PostgreSQL 9 张核心表 + 默认租户/管理员 + demo 数据
- 🐳 Podman Compose 基础服务可拉起（postgres、redis、qdrant）

### 规划中（Week 2+）

- JWT 认证 / refresh / logout / `/auth/me`（Week 2）
- RBAC 权限校验落地（Week 2）
- 知识库 CRUD API + 文档上传解析（Week 2）
- 对话 / 工单 CRUD API（Week 2）
- RAG 语义检索 + Qdrant 业务接入（Week 3）
- LangGraph 智能客服工作流（Week 3）
- 工单自动流转（Week 3）
- 全链路审计日志（Week 3）
- 前端管理后台（Week 3）
- Celery 异步任务业务闭环（Week 2+）

---

## 核心模块状态

| 模块 | 说明 | 当前状态 |
|------|------|----------|
| Auth | 登录认证、JWT 令牌管理 | mock 登录 ✅（JWT → Week 2） |
| Tenant | 多租户管理 & 数据隔离 | 模型层 ✅（API → Week 2） |
| User & RBAC | 用户管理 & 角色权限控制 | 模型层 ✅（权限校验 → Week 2） |
| Knowledge Base | 知识库创建、更新、统计 | 模型层 ✅（CRUD → Week 2） |
| Document | 文档上传、解析、切片、向量入库 | 模型层 ✅（解析 → Week 2） |
| RAG | 语义检索、重排择优、上下文拼接 | 规划中（Week 3） |
| Agent | LangGraph 智能客服工作流 | 规划中（Week 3） |
| Ticket | 工单创建、流转、指派、关闭 | 模型层 ✅（API → Week 2） |
| Audit Log | 全链路审计日志 & 汇总统计 | 规划中（Week 3） |
| Dashboard | 数据大盘 & 租户级统计 | 规划中（Week 3） |

---

## 业务流程

```
客户提交问题 → 问题自动分类 → 知识库语义检索 → AI 生成回复建议
  → 复杂问题转人工工单 → 全流程审计溯源
```

> 当前仅实现数据模型层和 mock 登录入口，业务流程闭环将在 Week 2+ 逐步落地。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js · TypeScript · Tailwind CSS · shadcn/ui |
| **后端** | FastAPI · PostgreSQL · Redis · Qdrant · Celery · Alembic |
| **智能体** | LangGraph · OpenAI 系列模型 |
| **评估** | Ragas |
| **部署** | Podman Compose |

---

## 项目结构

```
SupportForge/
├── frontend/            # 前端 Next.js 项目
├── backend/             # 后端 FastAPI 项目
├── docs/                # 项目文档 & 接口文档
├── deploy/              # 部署配置
├── scripts/             # 自动化脚本
├── compose.yml          # 一键部署（Podman Compose）
├── CLAUDE.md            # 开发规范
└── README.md            # 项目说明
```

### 后端结构

```
backend/app/
├── main.py              # 项目入口
├── core/                # 全局配置、依赖、中间件
├── db/                  # 数据库连接 & 会话管理
├── models/              # ORM 实体模型（9 张核心表）
├── schemas/             # Pydantic 请求/响应模型
├── api/v1/              # API v1 路由（health + auth mock）
├── services/            # 业务逻辑层（Week 2 落地）
├── repositories/        # 数据操作层（Week 2 落地）
├── agent/               # LangGraph 智能体（Week 3）
├── rag/                 # RAG 知识库逻辑（Week 3）
├── tasks/               # Celery 异步任务（Week 2+）
├── integrations/        # 第三方集成
└── utils/               # 工具函数
```

---

## 快速启动

### 后端本地开发

```bash
cd backend
poetry install --with dev
poetry run alembic upgrade head
poetry run python -m app.db.init_db
poetry run python scripts/init_demo_data.py
poetry run uvicorn app.main:app --reload
```

启动后访问以下入口验证：

- Swagger UI: http://localhost:8000/docs
- 健康检查: `curl http://localhost:8000/api/v1/health`
- Mock 登录: `curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"admin@acme.com","password":"123456"}'`

> 当前登录仅支持默认管理员 `admin@acme.com`，返回 mock token。JWT 完整认证留到 Week 2。

### 前端

```bash
cd frontend
npm install
npm run dev
```

### Podman Compose 全栈启动

```bash
podman compose up -d
```

> compose 场景需要先配置 `backend/.env.compose`（已提供模板，连接地址使用 compose 服务名而非 localhost）。
> `celery-worker` 当前因 `app.tasks.celery_app` 模块尚未实现而无法正常运行，这是预期行为。

---

## 项目定位

本项目为 **秋招面试核心实战项目**，重点关注：

- ✅ 商业业务闭环（非玩具 Demo）
- ✅ 多租户隔离架构
- ✅ 后端工程深度
- ✅ AI Agent 工作流成熟度

详细开发规范请参见 [CLAUDE.md](./CLAUDE.md)。