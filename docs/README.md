# SupportForge 项目文档

> 原大文档已拆分为以下独立模块，便于查找和维护。

---

## 📁 需求文档 (`docs/requirements/`)

| 文件 | 内容 |
|------|------|
| [项目需求清单.md](requirements/项目需求清单.md) | 必须补齐清单、建议补齐、可选加分项、优先 8 件事、面试视角 |
| [开发里程碑.md](requirements/开发里程碑.md) | 6 周开发计划、交付物、每周检查标准 |
| [里程碑与目录对应.md](requirements/里程碑与目录对应.md) | 每周里程碑对应的目录/文件、重点目录、按域开发策略 |
| [示例测试数据.md](requirements/示例测试数据.md) | Demo 初始化数据（租户、用户、知识库、文档、对话、工单、审计日志） |

---

## 📁 接口文档 (`docs/api/`)

| 文件 | 内容 |
|------|------|
| [通用约定.md](api/通用约定.md) | 统一前缀、返回结构、分页结构、认证方式 |
| [auth.md](api/auth.md) | 认证接口：登录、刷新 Token、获取用户信息、退出 |
| [tenants.md](api/tenants.md) | 租户接口：创建、列表、详情、更新、禁用/启用 |
| [users.md](api/users.md) | 用户接口：创建、列表、详情、更新、删除、修改角色 |
| [knowledge-bases.md](api/knowledge-bases.md) | 知识库接口：创建、列表、详情、更新、删除、统计 |
| [documents.md](api/documents.md) | 文档接口：上传、列表、详情、删除、重解析、状态查询 |
| [conversations.md](api/conversations.md) | 对话接口：创建、列表、详情、发送消息、消息列表、关闭 |
| [tickets.md](api/tickets.md) | 工单接口：创建、列表、详情、更新状态、指派、关闭、备注 |
| [audit-logs.md](api/audit-logs.md) | 审计日志接口：列表、详情、汇总统计 |
| [agent-metrics-priority.md](api/agent-metrics-priority.md) | Agent 接口、统计接口、开发优先级 |

---

## 📁 架构文档 (`docs/architecture/`)

| 文件 | 内容 |
|------|------|
| [项目结构与文件职责.md](architecture/项目结构与文件职责.md) | 仓库结构、后端各层文件职责、前端文件职责、开发顺序 |
| [数据表设计.md](architecture/数据表设计.md) | 9 张核心表的 SQL 定义、索引设计、前端页面列表 |

---

## 📁 开发 Spec (`docs/spec/`)

| 文件 | 内容 |
|------|------|
| [day8-auth-password-jwt-login.md](spec/day8-auth-password-jwt-login.md) | Day 8：Argon2 密码哈希、Access JWT 与真实登录闭环 |
| [day9-refresh-token-current-user.md](spec/day9-refresh-token-current-user.md) | Day 9：Refresh Token 轮换、当前用户依赖与登录租户路由 |

---

## 📁 Agent Prompt 文件（已创建为实际代码文件）

> 已直接写入 `backend/app/agent/prompts/` 目录，无需在文档中维护。

| 文件 | 路径 | 内容 |
|------|------|------|
| agent.md | `backend/app/agent/prompts/agent.md` | AI 助手角色定义与核心原则 |
| classify.md | `backend/app/agent/prompts/classify.md` | 问题分类提示词 |
| respond.md | `backend/app/agent/prompts/respond.md` | 回复生成提示词 |
| escalate.md | `backend/app/agent/prompts/escalate.md` | 转工单提示词 |
| system.md | `backend/app/agent/prompts/system.md` | 系统约束提示词 |
