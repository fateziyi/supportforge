# SupportForge

企业级 SaaS 智能客服 AI 平台 —— 多租户隔离、RAG 知识检索、LangGraph 智能体编排、工单自动流转。

---

## ✨ 核心特性

- 🏢 多租户 SaaS 架构，数据完全隔离
- 🔐 RBAC 权限体系（平台管理员 / 租户管理员 / 客服坐席 / 审计员）
- 📚 知识库管理 & 文档上传解析
- 🔍 RAG 语义检索（Qdrant 向量库）
- 🤖 LangGraph 智能体工作流编排
- 📋 复杂问题自动转人工工单
- 📝 全链路审计日志 & 行为溯源
- 🖥️ 前端管理后台仪表盘
- 🐳 Podman Compose 一键本地部署

---

## 🔄 业务流程

```
客户提交问题 → 问题自动分类 → 知识库语义检索 → AI 生成回复建议
  → 复杂问题转人工工单 → 全流程审计溯源
```

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js · TypeScript · Tailwind CSS · shadcn/ui |
| **后端** | FastAPI · PostgreSQL · Redis · Qdrant · Celery · Alembic |
| **智能体** | LangGraph · OpenAI 系列模型 |
| **评估** | Ragas |
| **部署** | Podman Compose |

---

## 📁 项目结构

```
SupportForge/
├── frontend/            # 前端 Next.js 项目
├── backend/             # 后端 FastAPI 项目
├── docs/                # 项目文档 & 接口文档
├── deploy/              # 部署配置
├── scripts/             # 自动化脚本
├── compose.yml            # 一键部署（Podman Compose）
├── CLAUDE.md            # 开发规范
└── README.md            # 项目说明
```

### 后端结构

```
backend/app/
├── main.py              # 项目入口
├── core/                # 全局配置、依赖、中间件
├── db/                  # 数据库连接 & 会话管理
├── models/              # ORM 实体模型
├── schemas/             # Pydantic 请求/响应模型
├── api/v1/              # API v1 路由
├── services/            # 业务逻辑层
├── repositories/        # 数据操作层
├── agent/               # LangGraph 智能体
├── rag/                 # RAG 知识库逻辑
├── tasks/               # Celery 异步任务
├── integrations/        # 第三方集成
└── utils/               # 工具函数
```

### 前端结构

```
frontend/src/
├── app/                 # Next.js 路由页面
├── components/ui/       # shadcn/ui 组件
├── features/            # 业务模块组件
├── hooks/               # 自定义 Hooks
├── lib/                 # 工具 & 请求封装
├── types/               # TS 类型定义
└── styles/              # 全局样式
```

---

## 🧩 核心模块

| 模块 | 说明 |
|------|------|
| Auth | 登录认证、JWT 令牌管理 |
| Tenant | 多租户管理 & 数据隔离 |
| User & RBAC | 用户管理 & 角色权限控制 |
| Knowledge Base | 知识库创建、更新、统计 |
| Document | 文档上传、解析、切片、向量入库 |
| RAG | 语义检索、重排择优、上下文拼接 |
| Agent | LangGraph 智能客服工作流 |
| Ticket | 工单创建、流转、指派、关闭 |
| Audit Log | 全链路审计日志 & 汇总统计 |
| Dashboard | 数据大盘 & 租户级统计 |

---

## 🚀 快速启动

### 后端

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### 全栈一键部署

```bash
podman compose up -d
```

---

## 📌 项目定位

本项目为 **秋招面试核心实战项目**，重点关注：

- ✅ 商业业务闭环（非玩具 Demo）
- ✅ 多租户隔离架构
- ✅ 后端工程深度
- ✅ AI Agent 工作流成熟度

详细开发规范请参见 [CLAUDE.md](./CLAUDE.md)。