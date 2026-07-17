# Week 2 每日任务拆分

> 主题：认证闭环、多租户逻辑隔离与 RBAC 权限基础
>
> 状态：进行中 🚧 | Day 8 ✅ | Day 9 ✅ | Day 10 ✅ | Day 11–14 待开发

---

## 本周核心目标

1. 用户身份只由 Access JWT 与数据库当前用户记录共同确认。
2. 租户数据访问必须强制带上可信 `tenant_id`，不信任前端传参。
3. 角色权限按 `platform_admin`、`tenant_admin`、`support_agent`、`auditor` 落地，并保证默认拒绝。
4. 为 Week 3 的知识库与文档 CRUD 提供可复用的认证、租户过滤和权限依赖。

### Week 2 完成标准

- 不同租户使用同一资源 ID 或伪造 tenant 参数时，无法读取或修改对方数据。
- Access / Refresh Token 生命周期、登出撤销和当前用户依赖可重复验证。
- 所有新增业务接口明确标注允许角色、读写动作和数据范围。
- 关键鉴权失败统一返回标准错误结构，且有自动化测试覆盖。

---

## Day 8：Argon2 密码哈希 + Access JWT + 真实登录 ✅

**目标**：把 Week 1 mock 登录替换为真实、可测试的本地认证闭环。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 使用 Argon2id 哈希存储与校验密码，升级默认管理员旧哈希 | `backend/app/core/security.py`、`backend/app/db/init_db.py` |
| 2 | 签发并解析 Access JWT，包含用户、租户、角色与 token 类型 | `backend/app/core/security.py` |
| 3 | 将登录业务下沉到 Repository + Service，删除 mock token | `backend/app/repositories/user_repo.py`、`backend/app/services/auth_service.py`、`backend/app/api/v1/auth.py` |
| 4 | 完成成功登录、错误密码、禁用用户、非法 token 与 API 契约测试 | `backend/tests/test_auth.py`、`backend/tests/test_api_contract.py` |
| 5 | 修复原始请求体校验错误被错误包装为 500 的问题 | `backend/app/core/exceptions.py` |

### 验证结果

- ✅ 登录返回真实 HS256 Access JWT，错误密码返回 `40100`。
- ✅ 默认管理员的 SHA-256 哈希已升级为 Argon2id。
- ✅ Ruff、Black、MyPy、pytest 全部通过。

### 对应 Spec

- [Day 8 Spec](../spec/day8-auth-password-jwt-login.md)

---

## Day 9：Refresh Token 轮换 + 当前用户依赖 + 登录租户路由 ✅

**目标**：完成可撤销的登录会话与可信当前用户上下文。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 增加租户 `slug`，为跨租户同邮箱登录提供安全路由 | `backend/app/models/tenant.py`、迁移、`init_db.py` |
| 2 | 新建只保存 `jti` 的 Refresh Session，支持轮换与撤销 | `backend/app/models/refresh_token_session.py`、`repositories/refresh_token_session_repo.py` |
| 3 | 新增 Refresh JWT 签发/解析、登录 token 对与原子轮换逻辑 | `backend/app/core/security.py`、`backend/app/services/auth_service.py` |
| 4 | 实现 `get_current_user()`，验证 token、用户与租户状态并注入 ContextVar | `backend/app/api/deps.py`、`backend/app/core/context.py` |
| 5 | 新增 `/auth/refresh`、`/auth/me`、`/auth/logout` | `backend/app/api/v1/auth.py`、`backend/app/schemas/auth.py` |

### 验证结果

- ✅ Refresh Token 单次轮换，旧 token 重放返回 `40100`。
- ✅ logout 后当前租户 Refresh Session 全部失效。
- ✅ `/auth/me` 只返回数据库中仍处于 active 状态的当前用户。

### 对应 Spec

- [Day 9 Spec](../spec/day9-refresh-token-current-user.md)

---

## Day 10：Tenant Scope 基础设施 + 多租户逻辑隔离 ✅

**目标**：让后续租户资源查询必须复用可信 Tenant Scope，而非依赖开发者手写过滤条件。

### 任务清单

| # | 任务 | 产出文件 |
|---|------|----------|
| 1 | 定义冻结 `TenantScope`，校验 ContextVar 与认证用户一致 | `backend/app/core/tenant_scope.py` |
| 2 | 新增 `TenantScopedRepository`，强制生成 `id + tenant_id` 查询条件 | `backend/app/repositories/base.py` |
| 3 | 实现当前租户 Repository、Service、Schema 和接口 | `tenant_repo.py`、`tenant_service.py`、`schemas/tenant.py`、`api/v1/tenants.py` |
| 4 | 挂载 `GET /api/v1/tenants/current` | `backend/app/api/v1/router.py` |
| 5 | 覆盖 scope 缺失、查询 tenant 条件和伪造参数无效等测试 | `backend/tests/test_tenant_scope.py`、`test_api_contract.py` |

### 验证结果

- ✅ `GET /api/v1/tenants/current?tenant_id=forged-tenant-id` 仍只返回认证用户所属租户。
- ✅ Ruff、Black、MyPy、pytest（12 passed）通过。

### 对应 Spec

- [Day 10 Spec](../spec/day10-tenant-scope-isolation.md)

---

## Day 11：知识库与文档的 Tenant Scoped CRUD（待开发）

**目标**：把 Day 10 的 Repository 边界应用到第一批实际业务资源，形成“可创建、可查询、不可跨租户访问”的最小业务闭环。

### 任务清单

| # | 任务 | 预期产出文件 |
|---|------|--------------|
| 1 | 定义知识库、文档创建/更新/列表/详情 DTO 与分页参数 | `backend/app/schemas/knowledge_base.py`、`schemas/document.py` |
| 2 | 实现 KnowledgeBase / Document 的 Tenant Scoped Repository | `backend/app/repositories/knowledge_base_repo.py`、`document_repo.py` |
| 3 | 实现业务 Service，统一将无结果映射为 `NotFoundException` | `backend/app/services/knowledge_base_service.py`、`document_service.py` |
| 4 | 新增知识库与文档基础 CRUD 路由，全部使用 `get_current_user` 和 Tenant Scope | `backend/app/api/v1/knowledge_bases.py`、`documents.py`、`router.py` |
| 5 | 覆盖双租户创建、列表、详情与跨租户 ID 访问 | `backend/tests/test_knowledge_base_api.py`、`test_document_api.py` |

### 验证标准

```bash
# 使用两个不同租户 token 创建数据
# 租户 A 请求租户 B 的 knowledge_base_id/document_id → 40400
# 列表接口仅返回本租户数据
```

---

## Day 12：RBAC 角色模型 + 权限依赖（待开发）

**目标**：建立默认拒绝的角色权限依赖，确保 API 可以声明“谁能做什么”。

### 任务清单

| # | 任务 | 预期产出文件 |
|---|------|--------------|
| 1 | 定义角色常量、合法角色集合与权限动作枚举 | `backend/app/core/permissions.py` |
| 2 | 实现 `require_roles(*roles)` 依赖工厂，未授权统一抛 `ForbiddenException` | `backend/app/api/deps.py` |
| 3 | 补充角色/操作/数据范围映射表与中文注释 | `docs/architecture/权限模型设计.md`（若已有同主题文档则增量更新） |
| 4 | 为已有租户、知识库、文档接口标注最低允许角色 | 路由文件与对应 API 文档 |
| 5 | 测试四类角色与默认拒绝行为 | `backend/tests/test_permissions.py` |

### 最小权限矩阵

| 角色 | 当前租户信息 | 知识库/文档读取 | 知识库/文档写入 | 审计读取 | 跨租户 |
|------|--------------|----------------|----------------|----------|--------|
| `platform_admin` | ✅ | Day 12 仅本租户 | Day 12 仅本租户 | Day 14 | Day 14 显式分支 |
| `tenant_admin` | ✅ | ✅ | ✅ | Day 14 | ❌ |
| `support_agent` | ✅ | ✅ | 仅业务允许的有限操作 | Day 14 | ❌ |
| `auditor` | ✅ | 只读 | ❌ | Day 14 | ❌ |

---

## Day 13：用户管理 + 租户内角色分配（待开发）

**目标**：让租户管理员能够在本租户范围内管理用户、启停账号和分配合法角色。

### 任务清单

| # | 任务 | 预期产出文件 |
|---|------|--------------|
| 1 | 定义用户创建、更新、状态和角色变更 DTO | `backend/app/schemas/user.py` |
| 2 | 实现 Tenant Scoped User Repository / Service | `backend/app/repositories/user_management_repo.py`、`services/user_service.py` |
| 3 | 新增用户列表、创建、更新、启停、角色变更接口 | `backend/app/api/v1/users.py`、`router.py` |
| 4 | 使用 `require_roles("tenant_admin")` 保护写接口 | `backend/app/api/deps.py`、用户路由 |
| 5 | 防止管理员修改其他租户用户或将自身降权导致不可恢复 | Service 测试与业务规则 |

### 验证标准

- 租户管理员只能管理本租户用户。
- `support_agent`、`auditor` 调用写接口返回 `40300`。
- 修改用户状态后，该用户的 `/auth/me` 与 refresh 行为符合状态校验规则。

---

## Day 14：权限回归 + 越权审计准备 + Week 2 收口（待开发）

**目标**：对认证、租户隔离、RBAC 做端到端验证，并为后续审计日志模块准备一致的越权事件模型。

### 任务清单

| # | 任务 | 预期产出文件 |
|---|------|--------------|
| 1 | 增加跨租户、跨角色、过期/撤销 token 的回归测试矩阵 | `backend/tests/test_authorization_matrix.py` |
| 2 | 定义越权访问的结构化日志字段和接入点，不提前写完整审计业务 | `backend/app/core/logging.py` 或 `docs/api/audit-logs.md` 增量更新 |
| 3 | 补齐 API 文档中每个已实现接口的角色、读写与数据范围说明 | `docs/api/*.md` |
| 4 | 运行双租户、四角色的手工冒烟脚本 | `scripts/verify_week2_auth.sh`（若引入脚本需纳入 CI 使用说明） |
| 5 | 更新 Week 2 完成状态、README、Spec 实现记录 | `docs/requirements/week2-daily-tasks.md`、相关 spec、`README.md` |

### Week 2 收口验证

```bash
cd backend
poetry run alembic upgrade head
poetry run ruff check app scripts tests
poetry run black --check app scripts tests
poetry run mypy app --ignore-missing-imports
poetry run pytest -q
```

手工验证至少包含：

1. 两个租户分别登录，互相不可读取资源。
2. Refresh Token 轮换、重放拦截、logout 撤销均有效。
3. 四类角色访问读写接口时结果符合权限矩阵。
4. 所有失败响应保持 `{code, message, data}` 统一结构。

---

## Week 2 当前状态与下一步

```text
Day 8  真实登录 / Access JWT                         ✅
Day 9  Refresh Token / 当前用户依赖 / 登录租户路由      ✅
Day 10 Tenant Scope / 当前租户受保护接口                ✅
Day 11 第一批 Tenant Scoped 业务 CRUD                  ⏳
Day 12 RBAC 角色与权限依赖                              ⏳
Day 13 租户内用户管理与角色分配                          ⏳
Day 14 权限回归、越权审计准备与 Week 2 收口              ⏳
```

> 注意：Day 10 已建立租户隔离基础，但只有在 Day 11 将它应用到实际业务 CRUD 后，才能证明业务数据层面的完整隔离；Day 12–14 的 RBAC 未完成前，`platform_admin` 也不得拥有隐式跨租户权限。
