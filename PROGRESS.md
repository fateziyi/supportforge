# 项目开发进度

## 当前版本

Week 1 / Day 7 收口版（2026-05-26）

## 已完成模块

1. FastAPI 应用入口 + Swagger UI 可访问
2. 配置管理（`app/core/config.py`）— Pydantic Settings + `.env` 读取
3. 结构化日志初始化（`app/core/logging.py`）
4. 统一异常处理 + 响应格式（`app/core/exceptions.py`）
5. JWT 签发/解析骨架（`app/core/security.py`）— 函数签名存在，Week 2 填充实现
6. 请求级上下文 ContextVar（`app/core/context.py`）
7. 数据库连接 + AsyncSession + ORM 基类（`app/db/session.py` + `app/db/base.py`）
8. Alembic 迁移框架（2 个迁移脚本，9 张核心表 + `alembic_version`）
9. 9 张核心 ORM 模型（tenant, user, knowledge_base, document, conversation, conversation_message, ticket, audit_log, agent_run）
10. Auth Schema（LoginRequest, TokenResponse, CurrentUserResponse）
11. Mock 登录接口（`POST /api/v1/auth/login`）— 仅支持默认管理员
12. 默认数据初始化脚本（`init_db.py`）— 默认租户 + 管理员，幂等
13. Demo 数据初始化脚本（`init_demo_data.py`）— KB + 文档 + 对话 + 工单，幂等
14. Podman Compose 配置（postgres, redis, qdrant, backend, frontend, celery-worker 定义）
15. CI Backend workflow（ruff + black + mypy + pytest 条件执行）
16. README 诚实化更新 + 启动说明

## 正在开发模块

无（Week 1 收口完成，准备进入 Week 2）

## 待开发模块

1. JWT 认证完整实现（签发、验证、refresh、logout、`/auth/me`）
2. Argon2 密码哈希替代 sha256 临时方案
3. RBAC 权限校验中间件 + `get_current_user()` 实现
4. KnowledgeBase CRUD API
5. Document 上传 + 解析 + 切片 + 向量入库
6. Conversation / ConversationMessage API
7. Ticket CRUD API + 状态流转
8. Celery 任务业务闭环（`app.tasks.celery_app` 模块实现）
9. RAG 语义检索 + Qdrant 业务接入
10. LangGraph 智能客服工作流
11. 全链路审计日志 API
12. 前端管理后台页面

## 数据库已建表

| 表名 | 说明 |
|------|------|
| `tenants` | 多租户表，当前含 1 条默认租户 |
| `users` | 用户表，当前含 1 条默认管理员 |
| `knowledge_bases` | 知识库表，当前含 1 条 demo 数据 |
| `documents` | 文档表，当前含 1 条 demo 数据 |
| `conversations` | 对话表，当前含 1 条 demo 数据 |
| `conversation_messages` | 对话消息表（空） |
| `tickets` | 工单表，当前含 1 条 demo 数据 |
| `audit_logs` | 审计日志表（空） |
| `agent_runs` | Agent 执行记录表（空） |
| `alembic_version` | 迁移版本追踪表 |

## 已完成接口

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/v1/health` | GET | 健康检查，返回 `{status: ok, service: supportforge-backend}` |
| `/api/v1/auth/login` | POST | Mock 登录，仅支持 `admin@acme.com`，返回 mock token + user |

## 当前技术难点

1. JWT 认证真正落地 — 需要实现签发、验证、refresh、黑名单，并替换 mock 阶段
2. Argon2 替换 — init_db.py 中的 sha256 临时密码哈希需替换为 argon2-cffi
3. 多租户上下文过滤 — 所有业务查询强制按 tenant_id 过滤，需中间件级实现
4. Celery Worker — compose 中已定义但业务模块未实现，Week 2 需创建 `app.tasks.celery_app`
5. Qdrant 业务接入 — 容器可启动但尚无业务代码与它交互

## 下周开发计划

Week 2（认证与基础 API 落地）：

1. Argon2 密码哈希实现 + 替换 init_db 临时方案
2. JWT 认证完整实现（签发、验证、refresh、logout）
3. `get_current_user()` 依赖注入实现
4. RBAC 权限校验中间件
5. KnowledgeBase / Document CRUD API
6. Celery 基础框架搭建