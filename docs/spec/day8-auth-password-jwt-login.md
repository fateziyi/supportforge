# Day 8 Spec：Argon2 密码哈希 + Access JWT + 真实登录

> 目标：把 Week 1 的 mock 登录替换为真实、可测试的本地登录闭环，为 Day 9 的刷新令牌和 `get_current_user()` 依赖提供稳定基础。

---

## 1. Day 8 要解决什么问题

Week 1 已有 `users` 表、默认管理员、`POST /api/v1/auth/login` 路径和统一响应格式，但当前登录只判断邮箱并返回固定 token；`init_db.py` 仍使用不适合密码存储的 SHA-256。

Day 8 必须解决：

1. 密码使用 Argon2 哈希存储与校验，禁止再写入或接受 SHA-256 作为正式密码哈希。
2. 登录从数据库读取用户，并校验用户状态与密码。
3. 登录成功签发可验证的 Access JWT；JWT 必须包含用户、租户、角色和令牌类型。
4. 保持现有路径与 `{code, message, data}` 顶层响应契约，避免前端联调漂移。
5. 用自动化测试证明成功登录、错误密码、禁用用户和非法 token 的行为。

---

## 2. Day 8 实现边界

### 2.1 Day 8 要做

| 范围 | 内容 |
|------|------|
| 密码安全 | 引入 `argon2-cffi`，实现哈希、校验和旧 SHA-256 识别/迁移策略 |
| JWT | 实现 Access Token 签发与解析，使用 HS256 和已有配置项 |
| 登录 | 替换 mock 逻辑：查用户 → 校验 `active` → 校验密码 → 签发 token |
| 初始化数据 | 默认管理员改用 Argon2；重复执行时可识别旧哈希并升级 |
| 审计准备 | 登录 Service 返回必要上下文；Day 8 不强制写审计表，但保留接入位置 |
| 测试 | 覆盖核心认证路径与响应契约 |

### 2.2 Day 8 不做

- 不实现 Refresh Token 的签发、轮换、撤销和黑名单（Day 9）。
- 不实现 `/auth/me`、`get_current_user()` 的真实依赖（Day 9）。
- 不实现 RBAC `require_roles()` 与租户 Repository 自动过滤（Day 10+）。
- 不提供注册、重置密码、修改密码或第三方 OAuth。
- 不将 Access Token 放入 Cookie；Day 8 仅返回 JSON，由前端后续统一处理。

---

## 3. 认证设计契约

### 3.1 Access JWT payload

| Claim | 类型 | 来源 | 说明 |
|------|------|------|------|
| `sub` | string | `users.id` | 用户 ID，唯一主体标识 |
| `tenant_id` | string | `users.tenant_id` | 后续业务隔离唯一可信来源 |
| `role` | string | `users.role` | 后续 RBAC 使用的角色快照 |
| `token_type` | string | 固定 `access` | Day 9 区分 refresh token |
| `iat` | datetime | 服务端生成 | 签发时间 |
| `exp` | datetime | 服务端生成 | 过期时间 |

约束：

- JWT 中不放密码、密码哈希、邮箱、模型密钥或任意用户输入。
- `tenant_id` 只能从已验证 token 中读取；任何后续接口不得信任前端传入 tenant ID。
- 解析失败、过期、缺 Claim、`token_type` 不为 `access` 都统一视为无效凭证。

### 3.2 登录响应

保持路径 `POST /api/v1/auth/login` 和已有响应结构不变：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "<jwt>",
    "refresh_token": "",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "...",
      "tenant_id": "...",
      "email": "admin@acme.com",
      "role": "tenant_admin"
    }
  }
}
```

Day 8 的 `refresh_token` 保留空字符串仅为兼容 Week 1 Schema；禁止伪造可用 refresh token。Day 9 实现后再返回真实值。

### 3.3 失败语义

| 场景 | HTTP | 业务码 | 对外消息 |
|------|------|--------|----------|
| 邮箱不存在或密码错误 | 401 | `40100` | `邮箱或密码错误` |
| 用户已禁用 | 403 | `40300` | `用户已被禁用` |
| 非法/过期/错误类型 Token | 401 | `40100` | `未登录或凭证无效` |

不得向前端区分“邮箱不存在”和“密码错误”，防止账号枚举。

---

## 4. 逐文件实现规格

### 4.1 `backend/pyproject.toml`

- 在主依赖增加 `argon2-cffi` 与 JWT 库（优先 `PyJWT`）。
- 不删除既有依赖；修改后执行 `poetry lock` 或 `poetry install`，确保锁文件同步。

### 4.2 `backend/app/core/security.py`

**职责**：认证基础设施，不访问数据库、不处理 HTTP 请求。

必须实现并写中文职责注释：

| 函数 | 输入 | 输出 | 规则 |
|------|------|------|------|
| `hash_password` | 明文密码 | Argon2 哈希 | 只在创建/重置密码调用 |
| `verify_password` | 明文、哈希 | bool | 兼容 Argon2；不能把异常泄露给调用方 |
| `create_access_token` | `user_id`、`tenant_id`、`role` | JWT string | 固定写入 §3.1 claims |
| `decode_access_token` | JWT string | 类型化 payload | 校验签名、过期、claim 和 `token_type=access` |

实现要求：

- token 过期时间基于 `settings.access_token_expire_minutes`，统一使用 UTC。
- JWT 库异常转换为项目的 `UnauthorizedException`，路由层不得直接处理库异常。
- 明文密码不得记录日志、不得放进 payload、不得写入异常消息。

### 4.3 `backend/app/repositories/user_repo.py`（新增）

**职责**：封装用户查询，不签 token、不写路由逻辑。

- 创建 `UserRepository`，构造参数为 `AsyncSession`。
- 实现 `get_by_email_for_login(email: str) -> User | None`。
- Day 8 登录不接受 tenant 参数，因此按 email 查询；后续若继续允许跨租户重复邮箱，Day 9 前必须补充明确的租户选择方案，不能静默 `scalar_one_or_none()`。

> 当前默认演示账号的邮箱唯一。正式多租户登录策略在 Day 9 前必须确定为“全局唯一邮箱”或“域名/租户 slug + 邮箱”。

### 4.4 `backend/app/services/auth_service.py`（新增）

**职责**：编排登录业务，路由只调用此 Service。

实现 `async authenticate(email: str, password: str) -> TokenResponse`：

1. 调用 Repository 查询用户。
2. 用户不存在或密码校验失败：抛出同一 `UnauthorizedException("邮箱或密码错误")`。
3. 用户状态不是 `active`：抛出 `ForbiddenException("用户已被禁用")`。
4. 调用 `create_access_token`，返回已有的 `TokenResponse`。
5. `refresh_token` 暂返回空字符串，`expires_in` 与 Settings 一致。

### 4.5 `backend/app/api/v1/auth.py`

- 删除 `DEFAULT_*` 常量和邮箱匹配 mock 逻辑。
- 注入 `AsyncSession = Depends(get_db)`，创建 `AuthService` 并调用 `authenticate`。
- 返回 `ApiResponse[TokenResponse]`；不得在路由层查询数据库、校验密码或拼装 JWT。
- 保持 `/api/v1/auth/login`、请求字段、成功响应外层结构不变。

### 4.6 `backend/app/db/init_db.py`

- 删除 `_temporary_password_hash` 和 `hashlib`。
- 默认管理员创建时使用 `hash_password(DEFAULT_ADMIN_PASSWORD)`。
- 已存在默认管理员若检测到非 Argon2 哈希，使用已知开发密码重新生成 Argon2 哈希并提交；仅限这个固定 demo 账号。
- 运行日志不得打印明文密码或哈希值。

### 4.7 `backend/tests/test_auth.py`（新增）

测试使用独立测试数据库或可控 Session fixture，禁止依赖开发库已有数据。

至少包含：

1. `hash_password` 结果不是明文，`verify_password` 成功/失败均符合预期。
2. 有效用户可登录；返回 token 可被 `decode_access_token` 解析，且 claims 正确。
3. 错误密码与不存在邮箱均返回相同 401 外部消息。
4. `disabled` 用户登录返回 403。
5. 篡改 token、过期 token、refresh 类型 token 均被拒绝。
6. 既有 `test_api_contract.py` 继续通过，确保顶层响应不漂移。

---

## 5. 实施顺序

1. 在 `pyproject.toml` 添加依赖并安装。
2. 实现、单测 `core/security.py` 的纯函数。
3. 改造 `init_db.py`，在本地数据库验证默认管理员哈希已升级。
4. 新建 Repository 与 Service。
5. 替换 auth 路由 mock 逻辑。
6. 补充 API/Service 测试。
7. 运行质量门禁与手动登录验证。
8. 所有验证通过后，在本 Spec 末尾回写“实现完成记录”。

---

## 6. 验证标准

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

手动验证：

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acme.com","password":"123456"}'
```

预期：HTTP 200；`data.access_token` 为真实 JWT；解码后包含 `sub`、`tenant_id`、`role`、`token_type=access` 与 `exp`。

---

## 7. Definition of Done

- [x] Argon2 依赖与锁文件同步。
- [x] 默认管理员不再存储 SHA-256 哈希。
- [x] mock 登录逻辑与固定 token 已删除。
- [x] 登录只通过 Service 层完成数据库查询、状态校验和密码校验。
- [x] Access JWT payload 与 §3.1 一致。
- [x] 错误信息不泄露账号是否存在。
- [x] 认证测试与 Week 1 契约测试均通过。
- [x] 本地手动登录与 Swagger/OpenAPI 验证通过。
- [x] 本文件已追加“实现完成记录”。

---

## 8. 实现完成记录

> 本章节记录 Day 8 spec 实际完成情况，包含产出文件、验证结果、与 spec 的偏差说明。

### 完成时间

2026-07-15

### 实际产出文件

| 文件 | 说明 |
|------|------|
| `backend/app/core/security.py` | 提供 Argon2id 密码哈希、Access JWT 签发和统一解码校验。 |
| `backend/app/core/config.py` | 将本地开发 JWT 默认密钥调整为符合 HS256 最低长度建议的值，并保留生产环境禁用默认值校验。 |
| `backend/app/repositories/user_repo.py` | 封装登录邮箱查询，并把跨租户同邮箱的歧义情况安全映射为认证失败。 |
| `backend/app/services/auth_service.py` | 编排密码校验、用户状态检查和 JWT 登录响应构造。 |
| `backend/app/api/v1/auth.py` | 将登录路由从 mock 替换为真实认证服务调用。 |
| `backend/app/db/init_db.py` | 默认管理员改用 Argon2id，并在重复执行时升级旧 sha256 演示哈希。 |
| `backend/tests/test_auth.py` | 覆盖密码、JWT、活跃账号、错误密码和禁用账号等认证核心场景。 |
| `backend/tests/test_api_contract.py` | 将登录接口契约测试改为依赖替换，避免 CI 依赖外部数据库。 |
| `backend/pyproject.toml`、`backend/poetry.lock` | 增加 `argon2-cffi` 与 `pyjwt` 依赖锁定。 |

### 验证结果

- ✅ `poetry run ruff check app scripts tests` → All checks passed。
- ✅ `poetry run black --check app scripts tests` → 45 个文件均无需格式化。
- ✅ `poetry run mypy app --ignore-missing-imports` → 44 个源文件无类型错误。
- ✅ `poetry run pytest -q` → 7 passed；覆盖 Argon2、JWT claims、篡改/过期/refresh token、成功登录、未知邮箱、错误密码、禁用账号及 API 响应契约。
- ✅ `poetry run alembic upgrade head` + `poetry run python -m app.db.init_db` → 迁移成功，已有默认管理员的旧 SHA-256 哈希已升级为 Argon2id。
- ✅ `POST /api/v1/auth/login` 使用 `admin@acme.com / 123456` → HTTP 200，返回真实 HS256 Access JWT、空 refresh token、1800 秒过期时间与正确的用户/租户信息。
- ✅ 同接口使用错误密码 → HTTP 401，响应为 `{ "code": 40100, "message": "邮箱或密码错误", "data": null }`。
- ✅ `GET /openapi.json` → HTTP 200，登录接口已暴露在 Swagger/OpenAPI 文档。

### 与 Spec 的偏差

1. **歧义邮箱处理**：由于现有数据模型允许不同租户使用同一邮箱，Day 8 的无 tenant_id 登录入口无法安全选定账号；实现明确拒绝选择任一账号，并按统一认证失败对外返回。租户登录入口设计仍留待 Day 9 统一确定。
2. **Refresh Token**：保持 `refresh_token` 为空字符串，仅用于既有响应 Schema 兼容；未生成任何可用 Refresh Token。
3. **JWT 默认密钥**：为消除 HS256 密钥长度告警，开发默认密钥调整为不少于 32 字节；生产环境仍禁止使用默认值，必须通过 `JWT_SECRET_KEY` 覆盖。
