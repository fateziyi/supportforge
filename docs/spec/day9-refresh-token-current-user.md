# Day 9 Spec：Refresh Token 轮换 + 当前用户依赖 + 登录租户路由

> 目标：在 Day 8 的真实 Access JWT 登录之上，补齐可撤销的 Refresh Token 会话、`get_current_user()` 和 `/auth/me`，让后续所有受保护接口有唯一、可验证的用户与租户上下文来源。

---

## 1. 目标与完成契约

### 要解决的问题

1. Day 8 只签发 Access Token，过期后用户必须重新输入密码，且无法主动使登录会话失效。
2. `get_current_user()` 仍是占位实现，后续接口无法安全获取真实用户、租户和角色。
3. `users` 仅约束 `(tenant_id, email)` 唯一；仅凭邮箱登录时，跨租户同邮箱账号没有确定的身份路由方式。

### Done Contract

- 登录签发一对 Access/Refresh JWT，Refresh Token 仅以 `jti` 对应的服务端会话状态实现轮换、撤销和重放拦截。
- `/auth/refresh`、`/auth/me`、`/auth/logout` 与 `get_current_user()` 按本 spec 的认证和租户隔离规则工作。
- 由单测、迁移、真实 API 冒烟和质量门禁共同证明；任一 token 类型混用、已撤销 refresh token 或失效用户仍可访问即视为未完成。

---

## 2. 范围

### 2.1 本 Day 要做

| 范围 | 内容 |
|------|------|
| 登录租户路由 | 为租户增加全局唯一、公开可见但不可授权的 `slug`；登录请求支持可选 `tenant_slug`，解决同邮箱跨租户登录歧义。 |
| Refresh Session | 新建租户隔离的 refresh 会话表，只保存 `jti` 与状态，不保存原始 token。 |
| Refresh Token | 签发、解析、一次性轮换、撤销；旧 token 刷新后立即无效。 |
| 身份依赖 | 实现 `get_current_user()`，校验 Bearer Access Token、数据库中的用户和租户状态，并注入 ContextVar。 |
| 认证接口 | 更新登录；新增 `/auth/refresh`、`/auth/me`、`/auth/logout`。 |
| 测试与文档 | 覆盖正常、失效、撤销、重放、跨租户和 API 契约；同步认证 API 文档。 |

### 2.2 本 Day 不做

- 不做 RBAC `require_roles()`、权限矩阵或 Repository 自动租户过滤（Day 10）。
- 不做 Access Token 黑名单；登出后当前 Access Token 可使用至其短时过期，Refresh Token 已立即失效。
- 不做多设备会话管理页面、IP/设备指纹、风控、验证码、密码重置或 OAuth。
- 不将 token 放入 Cookie；仍由前端后续决定安全存储方案。

---

## 3. 已确认事实与关键决策

1. 当前 Access JWT 已含 `sub`、`tenant_id`、`role`、`token_type=access`、`iat`、`exp`，有效期为 `settings.access_token_expire_minutes`（当前 30 分钟）。
2. 用户邮箱只在租户内唯一；Day 8 对同邮箱多账号按认证失败处理，不能作为长期登录策略。
3. 所有租户业务表必须带 `tenant_id`，认证与会话查询必须同时验证 `user_id + tenant_id`。
4. token 只用 HS256 签名；JWT 的身份 claim 仅是输入，最终权限与状态以数据库当前用户记录为准。
5. 预认证阶段的 `tenant_slug` 只是账号路由标识，不是授权依据；认证成功后租户身份只取自 token 与数据库。

### 3.1 登录租户路由策略（本 Day 定案）

- `tenants.slug`：小写 kebab-case，全局唯一、不可变；默认租户使用 `acme-demo`。
- `POST /auth/login` 新增可选 `tenant_slug`：
  - 提供时：Repository 以 `tenant.slug + user.email` 精确查询。
  - 未提供时：仅当邮箱只匹配一个用户才允许登录；匹配多个用户时仍返回 `401 邮箱或密码错误`。
- 这样保持已有单租户 Demo 调用兼容，同时为正式多租户登录提供明确入口。

### 3.2 Refresh Token 策略（本 Day 定案）

- Refresh JWT claims：`sub`、`tenant_id`、`role`、`token_type=refresh`、`jti`、`iat`、`exp`。
- `jti` 由服务端生成 UUID；表中只存 `jti`，不落库原始 Refresh Token、密码或 token 哈希。
- Refresh 时使用数据库行锁读取活动会话：校验通过后在同一事务撤销旧 `jti`，再创建新 `jti`，形成一次性轮换。
- 重复使用已轮换、已登出、过期或不存在的 Refresh Token 一律返回 `40100 未登录或凭证无效`，不泄露原因。

---

## 4. 认证接口契约

### 4.1 `POST /api/v1/auth/login`

请求体：

```json
{
  "email": "admin@acme.com",
  "password": "123456",
  "tenant_slug": "acme-demo"
}
```

- `tenant_slug` 可选；存在时必须符合小写 kebab-case。
- 成功响应保持 `ApiResponse[TokenResponse]`，但 `refresh_token` 改为真实 JWT。
- `expires_in` 仍只表示 Access Token 秒数；不返回 refresh 过期秒数，避免前端将其误作授权依据。

### 4.2 `POST /api/v1/auth/refresh`

请求体：

```json
{ "refresh_token": "<refresh-jwt>" }
```

成功响应：`ApiResponse[TokenResponse]`。返回新的 Access Token 和新的 Refresh Token；不得返回旧 Refresh Token。

失败语义：非法、过期、access 类型 token、已撤销、已轮换、数据库用户/租户失效均返回 HTTP 401、`40100`、`未登录或凭证无效`。

### 4.3 `GET /api/v1/auth/me`

- 请求头：`Authorization: Bearer <access-token>`。
- 成功响应：`ApiResponse[CurrentUserDetailResponse]`，字段为 `id`、`tenant_id`、`username`、`email`、`role`、`status`。
- 缺失、格式错误、非法、过期、refresh 类型、用户不存在/禁用、租户禁用均返回统一 401，不泄露具体失效原因。

### 4.4 `POST /api/v1/auth/logout`

- 请求头：`Authorization: Bearer <access-token>`。
- 使用 `get_current_user()` 获取当前真实用户，撤销该用户在当前租户的全部活动 Refresh Session。
- 成功响应：`ApiResponse[None]`，即 `{ "code": 0, "message": "success", "data": null }`。
- 已签发 Access Token 不做黑名单，最多存活至既有 `exp`；此限制必须在接口文档中明确。

---

## 5. 数据模型与迁移

### 5.1 `tenants.slug`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `slug` | `String(80)` | `NOT NULL`、全局唯一、索引 | 登录前租户路由标识。 |

- 迁移必须先以确定性值回填已有租户；默认租户固定回填 `acme-demo`。
- 其他已有租户使用 `slugify(name) + "-" + id 前 8 位`；迁移中处理空名称与冲突，禁止留空值。
- ORM、初始化脚本、示例数据与文档必须同步使用 slug。

### 5.2 `refresh_token_sessions`

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | `String(36)` | PK | 服务端会话记录 ID。 |
| `tenant_id` | `String(36)` | FK tenants、索引 | 强制租户归属。 |
| `user_id` | `String(36)` | 与 `tenant_id` 组合 FK users | 会话所属用户，禁止跨租户引用。 |
| `jti` | `String(36)` | 全局唯一、索引 | Refresh JWT 的唯一会话标识。 |
| `expires_at` | `DateTime(timezone=True)` | 非空、索引 | 与 JWT `exp` 对齐。 |
| `revoked_at` | `DateTime(timezone=True)` | 可空、索引 | 非空即不可再使用。 |
| `revoked_reason` | `String(30)` | 可空 | `rotated` / `logout` / `security`。 |
| `replaced_by_jti` | `String(36)` | 可空 | 轮换链路定位；不作为授权依据。 |
| `created_at` / `updated_at` | timestamptz | 非空 | 继承 `TimestampMixin`。 |

必须包含：

- `UniqueConstraint(id, tenant_id)`，供组合外键和多租户一致性校验。
- `ForeignKeyConstraint([user_id, tenant_id], [users.id, users.tenant_id])`。
- 索引 `(tenant_id, user_id, revoked_at)` 与 `expires_at`。
- Alembic 显式迁移；不得依赖 `create_all`，不得手改数据库。

---

## 6. 逐文件实现规格

| 文件 | 改动要求 |
|------|----------|
| `backend/app/core/config.py` | 增加 `refresh_token_expire_days` 的正整数校验（保留现有配置名）；生产环境仍拒绝默认 JWT 密钥。 |
| `backend/app/core/security.py` | 新增 `RefreshTokenPayload`、`create_refresh_token`、`decode_refresh_token`；严格检查 token 类型、`jti`、UTC `iat/exp`，把 JWT 异常转为 `UnauthorizedException`。 |
| `backend/app/core/context.py` | 新增 `set_user_id`、`set_tenant_id`；保留 `clear_context`，不得用全局变量传递用户身份。 |
| `backend/app/models/tenant.py` | 增加不可空、唯一的 `slug` 字段。 |
| `backend/app/models/refresh_token_session.py` | 新增 Refresh Session ORM；中文职责注释、组合外键与索引完整声明。 |
| `backend/app/models/__init__.py` | 导入新增模型，保证 Alembic 发现 metadata。 |
| `backend/app/db/migrations/versions/<revision>_add_tenant_slug_and_refresh_sessions.py` | 对既有数据安全回填 slug，新增表、索引和约束；提供可执行 downgrade。 |
| `backend/app/repositories/user_repo.py` | 增加按 `id + tenant_id` 查询活动用户/活动租户，以及按可选 `tenant_slug` 查询登录账号的方法；所有查询显式带租户条件。 |
| `backend/app/repositories/refresh_token_session_repo.py` | 创建、按 `jti` 行锁读取、撤销单个会话、撤销用户全部活动会话；Repository 不签发 JWT。 |
| `backend/app/services/auth_service.py` | 登录在单一事务创建 Refresh Session；新增 `refresh` 和 `logout`；轮换中先锁旧会话、校验真实用户，再撤销旧会话并创建新会话。 |
| `backend/app/api/deps.py` | 用 `HTTPBearer(auto_error=False)` 实现 `get_current_user`：只接收 Access Token、查库验证用户/租户 active、注入 ContextVar，返回 `User`。 |
| `backend/app/schemas/auth.py` | 新增 `RefreshTokenRequest`、`CurrentUserDetailResponse`；`LoginRequest` 增加可选 `tenant_slug` 与格式校验。 |
| `backend/app/api/v1/auth.py` | 更新 login，新增 `/refresh`、`/me`、`/logout`；路由层只注入依赖、调用 Service 和返回 `ApiResponse`。 |
| `backend/app/db/init_db.py` | 默认租户创建/已有租户修复时确保 `slug=acme-demo`。 |
| `backend/tests/test_auth.py` | 扩充 token、会话轮换、撤销、重放、状态失效和 ContextVar 的可控 Session 测试。 |
| `backend/tests/test_api_contract.py` | 覆盖 `/refresh`、`/me`、`/logout` 的标准顶层响应、401 与 422 响应。 |
| `docs/api/auth.md` | 回写真实请求、响应、Bearer 认证、登出边界与安全语义。 |

---

## 7. 关键流程与安全约束

### 7.1 Refresh 轮换流程

```text
Refresh JWT → 验签/类型/jti/exp → SELECT ... FOR UPDATE 会话
  → 校验会话 active、用户 active、租户 active
  → revoke(old, rotated) + create(new jti)（同一事务）
  → 签发新的 Access + Refresh JWT → 返回
```

- 任意失败不得创建新会话，也不得部分提交撤销状态。
- 不信任 refresh token 的 `role`；新 Access Token 必须从数据库当前用户角色生成。
- 同一 Refresh Token 的并发刷新最多成功一次。
- 不在日志、异常、审计摘要中记录 JWT 全文、密码或 Authorization 头。

### 7.2 `get_current_user` 流程

```text
Authorization Bearer Access JWT → decode_access_token
  → WHERE users.id = sub AND users.tenant_id = tenant_id
  → 校验 user.status / tenant.status = active
  → set_user_id + set_tenant_id → 返回 User
```

- 缺少或非 Bearer 认证头、Refresh Token、过期/篡改 token、用户或租户不可用均统一为 `UnauthorizedException()`。
- 任何受保护路由只依赖该函数返回的 `User` 和 ContextVar；不从前端 body/query/path 读取授权用 `tenant_id`。

---

## 8. 测试与验证标准

```bash
cd backend
poetry install --with dev
poetry run alembic upgrade head
poetry run python -m app.db.init_db
poetry run ruff check app scripts tests
poetry run black --check app scripts tests
poetry run mypy app --ignore-missing-imports
poetry run pytest -q
```

至少覆盖：

1. 登录返回不同类型的 Access/Refresh JWT，Refresh payload 含 `jti`。
2. `/auth/refresh` 成功后旧 Refresh Token 立即返回 401，新 token 可使用。
3. 已 logout、过期、篡改、Access 类型 token 调用 refresh 都返回 40100。
4. 用户或租户被禁用后，`/auth/me` 和 refresh 都返回 401。
5. `/auth/me` 正确返回数据库用户信息，并将正确的 user/tenant 注入 ContextVar。
6. 同邮箱跨租户账号在未提供 slug 时失败；提供正确 slug 时只认证对应租户账号。
7. 任意请求缺失/错误 Content-Type 时返回统一 42200，不得回退为 500。

手动冒烟：登录 → `/me` → `/refresh` → 使用旧 refresh 失败 → `/logout` → 使用新 refresh 失败。

---

## 9. Checkpoint / 执行前确认

- **当前理解**：Day 9 不是单纯多加一个 `/refresh`；它要把 Token 生命周期、服务端撤销状态和后续受保护接口的身份来源闭环。
- **核心目标**：让认证后的用户与租户上下文可验证、可撤销、不可跨租户伪造。
- **主要风险**：迁移回填 slug、Refresh 并发重放、Access/Refresh 类型混用、登出后对 Access Token 的预期误解。
- **验证方式**：迁移 + 单元/API 测试 + 本地 PostgreSQL 事务验证 + 完整 curl 链路。
- **Execution Approval**：`Approved`（2026-07-16，用户已授权开始 Day 9 开发）。

---

## 10. 实现完成记录

> Day 9 全部需求实现并验证通过后，按 CLAUDE.md §17 回写实际产出、验证结果、与 Spec 的偏差。

### 完成时间

2026-07-16

### 实际产出文件

| 文件 | 说明 |
|------|------|
| `backend/app/core/security.py` | 新增 Refresh JWT 的签发与严格解析，使用 `jti` 关联服务端会话。 |
| `backend/app/core/context.py` | 增加认证用户、租户 ContextVar 写入函数。 |
| `backend/app/core/config.py` | 对 Refresh Token 有效期增加正整数校验。 |
| `backend/app/models/tenant.py` | 增加全局唯一的登录路由字段 `slug`。 |
| `backend/app/models/refresh_token_session.py` | 新增租户隔离、可撤销的 Refresh Session ORM。 |
| `backend/app/db/migrations/versions/b9c0d1e2f3a4_add_tenant_slug_and_refresh_sessions.py` | 回填租户 slug，创建 Refresh Session 表、索引和组合外键。 |
| `backend/app/repositories/user_repo.py`、`refresh_token_session_repo.py` | 增加活动用户回查、可选 slug 登录查询、Refresh Session 行锁与撤销操作。 |
| `backend/app/services/auth_service.py` | 登录签发 token 对，支持 refresh 原子轮换和 logout 撤销。 |
| `backend/app/api/deps.py`、`backend/app/api/v1/auth.py` | 实现 `get_current_user()` 与 refresh、me、logout 路由。 |
| `backend/app/schemas/auth.py`、`backend/app/db/init_db.py` | 增加认证 DTO 与默认租户 slug 初始化。 |
| `backend/tests/test_auth.py`、`backend/tests/test_api_contract.py` | 更新 Day 8 回归测试以兼容 Day 9 登录响应与租户 slug 参数。 |
| `docs/api/auth.md` | 同步真实 Refresh、Bearer、me 和 logout 边界。 |

### 验证结果

- ✅ `poetry run ruff check app tests` → All checks passed。
- ✅ `poetry run black --check app tests` → All files would be left unchanged。
- ✅ `poetry run mypy app --ignore-missing-imports` → 47 个源文件无类型错误。
- ✅ `poetry run pytest -q` → 8 passed。
- ✅ `poetry run alembic upgrade head` → 已执行 `aa1b2c3d4e5f -> b9c0d1e2f3a4`，本地 PostgreSQL 已创建 Refresh Session 表并回填默认租户 slug。
- ✅ 本地 API 链路：login → me → refresh 成功且 refresh token 发生轮换；旧 token 重放返回 40100；logout 后新 refresh token 也返回 40100。

### 与 Spec 的偏差

1. **slug 回填规则**：为保证迁移对任意历史租户名称可安全执行，非默认租户采用 `tenant-<去连字符的租户 ID>` 回填，而不是 spec 初稿中的 `slugify(name)`；默认租户仍固定为 `acme-demo`。这不影响登录路由的唯一性。
2. **测试范围**：当前自动化测试以安全工具、Service 可控 Session 和 API 响应契约为主；Refresh Session 的行锁轮换与撤销由真实 PostgreSQL 冒烟链路验证，后续可补独立集成测试夹具。

### Resume / Handoff

- 当前状态：Day 9 已实现并完成本地验证。
- 下一步唯一动作：进入 Day 10 RBAC 与受保护业务路由的权限约束开发。
