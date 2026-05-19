# Agent 项目完整需求及开发里程碑

# agent项目完整需求

## 一、必须补齐：项目最低生产化清单

### 1\. 基础工程结构

- 统一的项目目录结构

- `config` 分环境配置（dev / test / prod）

- `\.env` 管理敏感配置

- 统一日志初始化

- 统一异常处理

- 统一响应格式

### 2\. 数据库与迁移

- PostgreSQL 正式建表

- Alembic 迁移脚本

- 所有核心表明确索引

- `tenant\_id`、`user\_id`、`created\_at`、`updated\_at` 规范化

- 关键字段唯一性约束

- 外键约束与级联策略明确

### 3\. 多租户隔离

- 所有租户相关表强制带 `tenant\_id`

- 查询层必须自动过滤租户数据

- 创建数据时自动注入当前租户

- 不能依赖前端传来的 `tenant\_id`

- 管理员越权访问要有显式审计

### 4\. 认证与权限

- JWT 登录认证

- Access Token / Refresh Token 基础流程

- RBAC 权限控制

- 至少区分：

    - 平台管理员

    - 租户管理员

    - 客服人员

- 关键接口加鉴权依赖

### 5\. 核心业务闭环

必须跑通这一条主线：

- 客服问题进入

- 问题分类

- 检索知识库

- 生成回复建议

- 复杂问题转工单

- 保存审计记录

### 6\. RAG 数据链路

- 文档上传

- 文档解析

- 文档切分

- 向量化

- 入库 Qdrant

- 检索时 tenant 过滤

- 检索结果返回可追溯来源

### 7\. Agent 工作流

- LangGraph 状态流转清晰

- 每个节点职责明确

- 分类失败、检索失败、生成失败要有兜底逻辑

- 支持人工接管 / Human\-in\-the\-loop

- 关键状态可持久化

### 8\. 异步任务

- 文档解析异步化

- 向量入库异步化

- 大任务状态可查询

- 失败任务可重试

- 任务日志可追踪

### 9\. 审计与日志

- 记录每次 AI 请求

- 记录输入、输出、耗时、token 消耗

- 记录 tenant、user、request\_id

- 记录工单流转过程

- 便于面试时讲“可观测性”

### 10\. 部署可运行

- Docker Compose 一键启动

- 后端、前端、PostgreSQL、Redis、Qdrant 都能拉起

- README 写清楚启动步骤

- 提供 demo 数据初始化脚本

## 二、强烈建议补齐：让项目更像企业系统

### 1\. 查询性能优化

- 常用字段加索引

- 分页查询

- 避免全表扫描

- Qdrant 检索加 metadata filter

- 热点数据可加 Redis 缓存

### 2\. 安全增强

- 密码哈希存储

- Token 过期与刷新机制

- 接口限流

- 上传文件类型校验

- 防止越权访问

- 敏感日志脱敏

### 3\. 测试体系

- 核心 service 单测

- API 接口测试

- 多租户隔离测试

- RAG 检索测试

- Agent 工作流测试

### 4\. 前端闭环

- 登录页

- 知识库上传页

- 对话调试页

- 工单列表页

- 审计日志页

- 基础权限路由控制

### 5\. 可观测性

- 请求链路 ID

- 结构化日志

- 基础指标统计

- Agent tracing

- 错误告警预留接口

## 三、可选加分项：有的话更亮眼

- Ragas 评测报告

- 检索召回率对比实验

- 多轮对话记忆优化

- Rerank 对比效果展示

- 复杂问题自动转 Jira

- 多租户配额限制

- 成本统计面板

- 管理员全局视图

- 代码生成或回复模板配置化

## 四、你这个项目最建议优先做的 8 件事

1. 多租户逻辑隔离

2. JWT \+ RBAC

3. 文档上传到知识库

4. Qdrant 检索

5. LangGraph 闭环工作流

6. 工单转流转

7. 审计日志

8. Docker Compose 部署

## 五、面试官视角：什么叫“补齐了”

- 不是只有一个 prompt 接口

- 不是只有“上传文档 → 聊天”

- 有租户隔离

- 有权限控制

- 有异步任务

- 有审计

- 有失败兜底

- 有部署

- 有测试意识

# 项目开发里程碑清单

## 第 1 周：项目骨架与基础设施

### 要完成的内容

- 初始化前端 Next\.js \+ TypeScript \+ Tailwind CSS \+ shadcn/ui

- 初始化后端 FastAPI 项目结构

- 配置 PostgreSQL、Redis、Qdrant、Docker Compose

- 设计基础目录结构

- 配置 `\.env` 和分环境配置

- 搭建统一日志和统一异常处理

- 建立数据库连接与基础模型

### 交付物

- 项目能本地启动

- 前后端基础页面可访问

- 数据库和中间件容器可正常运行

## 第 2 周：认证、多租户与 RBAC

### 要完成的内容

- 用户登录与 JWT 认证

- Access Token 基础流程

- 当前用户上下文获取

- `tenant\_id` 注入机制

- 多租户逻辑隔离实现

- RBAC 权限模型

- 至少定义三类角色：

    - 平台管理员

    - 租户管理员

    - 客服人员

- 关键接口加权限校验

### 交付物

- 用户登录后能进入对应租户

- 不同租户的数据互相不可见

- 不同角色权限不同

## 第 3 周：知识库与 RAG 链路

### 要完成的内容

- 知识库创建与管理

- 文档上传

- 文档解析

- 文档切分

- 向量化

- 入库 Qdrant

- 检索接口

- 检索结果返回来源信息

- tenant 级过滤

### 交付物

- 能上传文档到知识库

- 能基于租户检索知识

- 能返回带来源的回答片段

## 第 4 周：Agent 工作流与工单闭环

### 要完成的内容

- LangGraph 工作流搭建

- 问题分类节点

- 检索节点

- 回复生成节点

- 复杂问题转工单节点

- 人工接管机制

- 工单创建与流转

- 多轮上下文保存

### 交付物

- 客服问题能自动分流

- 简单问题可直接回复

- 复杂问题可转工单

- 闭环流程能完整演示

## 第 5 周：审计、异步任务与前端闭环

### 要完成的内容

- Celery 异步任务接入

- 文档解析异步化

- 向量入库异步化

- 任务状态查询

- 审计日志记录

- 请求链路追踪

- 前端管理后台补齐：

    - 登录页

    - 知识库页

    - 对话调试页

    - 工单页

    - 审计页

### 交付物

- 任务不会阻塞主流程

- 所有关键操作可追踪

- 前端有完整管理闭环

## 第 6 周：测试、部署与简历包装

### 要完成的内容

- 核心接口测试

- 多租户隔离测试

- RAG 检索测试

- Agent 流程测试

- Docker Compose 一键部署整理

- README 完善

- 准备项目截图和演示脚本

- 整理简历表述

- 准备面试问答

### 交付物

- 项目稳定可演示

- README 可让别人快速启动

- 简历描述可直接使用

- 面试时能讲清楚设计取舍

# 推荐的最小可交付版本

1. **多租户 \+ RBAC**

2. **知识库上传 \+ Qdrant 检索**

3. **LangGraph 闭环 Agent**

4. **工单转流转 \+ 审计日志**

# 每周检查标准

- 是否能跑起来

- 是否有完整业务闭环

- 是否有租户隔离

- 是否有权限控制

- 是否有异步任务

- 是否有审计追踪

- 是否能部署演示

- 是否能写进简历

# 一、推荐的总体仓库结构

```Bash
saas-support-ai/
├── frontend/                # Next.js 前端
├── backend/                 # FastAPI 后端
├── docs/                    # 项目文档、架构图、演示说明
├── deploy/                  # 部署相关配置
├── scripts/                 # 初始化、迁移、测试脚本
├── README.md
└── docker-compose.yml
```

# 二、后端目录结构：FastAPI \+ Agent \+ RAG

```Bash
backend/
├── app/
│   ├── main.py                  # FastAPI 入口
│   ├── core/
│   │   ├── config.py            # 配置管理
│   │   ├── logging.py           # 统一日志
│   │   ├── exceptions.py        # 统一异常
│   │   ├── security.py          # JWT / 密码加密
│   │   └── context.py           # 当前 tenant / request 上下文
│   │
│   ├── db/
│   │   ├── base.py              # ORM Base
│   │   ├── session.py           # DB Session
│   │   ├── init_db.py           # 初始化脚本
│   │   └── migrations/         # Alembic 迁移
│   │
│   ├── models/
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── knowledge_base.py
│   │   ├── document.py
│   │   ├── ticket.py
│   │   ├── conversation.py
│   │   ├── audit_log.py
│   │   └── ...
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── tenant.py
│   │   ├── user.py
│   │   ├── knowledge_base.py
│   │   ├── document.py
│   │   ├── ticket.py
│   │   ├── conversation.py
│   │   └── audit_log.py
│   │
│   ├── api/
│   │   ├── deps.py              # 依赖注入：current_user, tenant
│   │   └── v1/
│   │       ├── router.py        # 聚合路由
│   │       ├── auth.py
│   │       ├── tenants.py
│   │       ├── users.py
│   │       ├── knowledge_bases.py
│   │       ├── documents.py
│   │       ├── tickets.py
│   │       ├── conversations.py
│   │       └── audit_logs.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── tenant_service.py
│   │   ├── knowledge_service.py
│   │   ├── document_service.py
│   │   ├── ticket_service.py
│   │   ├── conversation_service.py
│   │   ├── audit_service.py
│   │   └── rag_service.py
│   │
│   ├── repositories/
│   │   ├── base.py
│   │   ├── tenant_repo.py
│   │   ├── user_repo.py
│   │   ├── knowledge_base_repo.py
│   │   ├── document_repo.py
│   │   ├── ticket_repo.py
│   │   ├── conversation_repo.py
│   │   └── audit_log_repo.py
│   │
│   ├── agent/
│   │   ├── graph.py             # LangGraph 主流程
│   │   ├── states.py            # Agent 状态定义
│   │   ├── nodes/
│   │   │   ├── classifier.py
│   │   │   ├── retriever.py
│   │   │   ├── responder.py
│   │   │   ├── ticket_creator.py
│   │   │   └── human_in_loop.py
│   │   ├── tools/
│   │   │   ├── ticket_tools.py
│   │   │   ├── knowledge_tools.py
│   │   │   └── audit_tools.py
│   │   └── prompts/
│   │       ├── classify.md
│   │       ├── respond.md
│   │       └── escalate.md
│   │
│   ├── rag/
│   │   ├── chunking.py          # 文档切分
│   │   ├── embedding.py         # 向量化
│   │   ├── retriever.py         # Qdrant 检索
│   │   ├── rerank.py            # 重排序
│   │   ├── ingestion.py         # 入库流程
│   │   └── evaluators.py        # Ragas 评估
│   │
│   ├── tasks/
│   │   ├── celery_app.py
│   │   ├── document_tasks.py
│   │   ├── embedding_tasks.py
│   │   ├── ticket_tasks.py
│   │   └── cleanup_tasks.py
│   │
│   ├── integrations/
│   │   ├── qdrant_client.py
│   │   ├── redis_client.py
│   │   ├── jira_client.py
│   │   └── tracing.py
│   │
│   └── utils/
│       ├── pagination.py
│       ├── ids.py
│       ├── time.py
│       └── helpers.py
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

# 三、前端目录结构：够用但完整

```Bash
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── login/
│   ├── dashboard/
│   ├── knowledge-bases/
│   ├── documents/
│   ├── conversations/
│   ├── tickets/
│   ├── audit-logs/
│   └── settings/
│
├── components/
│   ├── ui/
│   ├── layout/
│   ├── forms/
│   ├── tables/
│   ├── charts/
│   └── common/
│
├── features/
│   ├── auth/
│   ├── tenant/
│   ├── knowledge-base/
│   ├── document/
│   ├── conversation/
│   ├── ticket/
│   └── audit-log/
│
├── lib/
│   ├── api.ts
│   ├── auth.ts
│   ├── utils.ts
│   └── constants.ts
│
├── hooks/
├── types/
└── styles/
```

# 四、里程碑与目录结构的对应关系

## 第 1 周：项目骨架与基础设施

对应目录：

- `backend/app/core/`

- `backend/app/db/`

- `backend/app/models/`

- `backend/app/api/`

- `frontend/app/`

- `frontend/components/`

- `deploy/`

- `docker\-compose\.yml`

## 第 2 周：认证、多租户与 RBAC

对应目录：

- `backend/app/core/security\.py`

- `backend/app/core/context\.py`

- `backend/app/api/deps\.py`

- `backend/app/models/tenant\.py`

- `backend/app/models/user\.py`

- `backend/app/schemas/auth\.py`

- `backend/app/services/auth\_service\.py`

- `backend/app/repositories/user\_repo\.py`

- `backend/app/api/v1/auth\.py`

- `backend/app/api/v1/tenants\.py`

- `frontend/app/login/`

- `frontend/features/auth/`

## 第 3 周：知识库与 RAG 链路

对应目录：

- `backend/app/models/knowledge\_base\.py`

- `backend/app/models/document\.py`

- `backend/app/services/knowledge\_service\.py`

- `backend/app/services/document\_service\.py`

- `backend/app/rag/chunking\.py`

- `backend/app/rag/embedding\.py`

- `backend/app/rag/retriever\.py`

- `backend/app/rag/ingestion\.py`

- `backend/app/tasks/document\_tasks\.py`

- `backend/app/tasks/embedding\_tasks\.py`

- `backend/app/api/v1/knowledge\_bases\.py`

- `backend/app/api/v1/documents\.py`

- `frontend/app/knowledge\-bases/`

- `frontend/app/documents/`

## 第 4 周：Agent 工作流与工单闭环

对应目录：

- `backend/app/agent/graph\.py`

- `backend/app/agent/states\.py`

- `backend/app/agent/nodes/`

- `backend/app/agent/tools/`

- `backend/app/services/conversation\_service\.py`

- `backend/app/services/ticket\_service\.py`

- `backend/app/models/conversation\.py`

- `backend/app/models/ticket\.py`

- `backend/app/api/v1/conversations\.py`

- `backend/app/api/v1/tickets\.py`

- `frontend/app/conversations/`

- `frontend/app/tickets/`

## 第 5 周：审计、异步任务与前端闭环

对应目录：

- `backend/app/models/audit\_log\.py`

- `backend/app/services/audit\_service\.py`

- `backend/app/tasks/`

- `backend/app/integrations/tracing\.py`

- `backend/app/api/v1/audit\_logs\.py`

- `frontend/app/audit\-logs/`

- `frontend/components/tables/`

- `frontend/components/charts/`

## 第 6 周：测试、部署与简历包装

对应目录：

- `backend/tests/unit/`

- `backend/tests/integration/`

- `backend/tests/e2e/`

- `deploy/`

- `scripts/`

- `docs/`

- `README\.md`

# 五、你最应该重点写好的目录

1. `backend/app/agent/`

    - 体现 LangGraph 能力

2. `backend/app/rag/`

    - 体现 RAG 工程能力

3. `backend/app/core/`

    - 体现后端基础功

4. `backend/app/api/v1/`

    - 体现业务接口设计

5. `backend/app/models/`

    - 体现多租户、权限、审计的数据建模

6. `frontend/app/`

    - 体现平台闭环

# 六、一个很实用的建议：先按“功能域”开发，不要按技术分散写

按域推进：

- `knowledge\_base`

- `document`

- `conversation`

- `ticket`

- `audit`
每个域形成：

- model

- schema

- repository

- service

- API

- 前端页面

