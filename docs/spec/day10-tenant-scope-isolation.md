# Day 10 Spec：Tenant Scope 基础设施 + 多租户逻辑隔离

> 目标：将 Day 9 已验证的 `get_current_user()` 与 `tenant_id` ContextVar 转化为可复用、不可绕过的租户数据访问边界，为 Day 11 的业务 CRUD 和 Day 12–14 的 RBAC 提供安全基础。

---

## 1. 目标与完成契约

### 要解决的问题

1. Day 9 已能从 Access Token 得到可信 `tenant_id`，但 Repository 尚未形成统一的强制租户过滤约束。
2. 未来知识库、文档、对话、工单等查询若遗漏 `tenant_id`，会造成高风险跨租户数据泄露。
3. 当前没有最小受保护租户接口，无法用真实 API 证明“用户只能读取自己的租户”。

### Done Contract

- 所有后续租户业务 Repository 都能通过统一 `TenantScopedRepository` 取得可信 scope，并以 `(id, tenant_id)` 作为资源定位边界。
- `GET /api/v1/tenants/current` 仅返回登录用户所属且状态正常的租户；伪造 path/query/body 中的 tenant 标识不能改变结果。
- 静态检查、单元/API 测试与本地两租户数据验证证明：任何跨租户读取均得到标准 `40400`，不会返回另一租户资源。

---

## 2. 范围

### 2.1 本 Day 要做

| 范围 | 内容 |
|------|------|
| Tenant Scope | 定义类型化 `TenantScope`，唯一来源为 `get_current_user()` 与 ContextVar，不接收前端 `tenant_id`。 |
| Repository 基类 | 新增只读的 `TenantScopedRepository`，提供当前 scope、按 `(id, tenant_id)` 查询及必需 scope 校验。 |
| 租户查询闭环 | 新增 `TenantRepository`、`TenantService` 与 `GET /api/v1/tenants/current`。 |
| 越权防护 | 不存在、跨租户或已禁用租户统一返回 `NotFoundException`；避免枚举其他租户。 |
| 测试 | 覆盖缺少认证、正常租户、跨租户 ID、ContextVar 缺失和路由响应契约。 |
| 文档 | 更新 tenants API 文档，并记录后续业务 Repository 的必选使用方式。 |

### 2.2 本 Day 不做

- 不实现租户列表、创建、更新、禁用等平台管理 CRUD。
- 不实现 `require_roles()` 或角色权限矩阵；`platform_admin` 的全局分支留到 Day 12–14。
- 不为所有已有资源一次性补齐 CRUD；Day 11 将以知识库/文档等业务 Repository 落实本基类。
- 不信任任何 query/path/body 的 `tenant_id` 作为授权依据，也不提供“任意 tenant_id 切换”接口。

---

## 3. 已确认事实与设计决策

1. Day 9 的 `get_current_user()` 已验证 Access JWT、用户状态和租户状态，并写入 `user_id_ctx`、`tenant_id_ctx`。
2. 所有租户业务表已有 `tenant_id`；关键关联已使用数据库级组合外键约束跨租户引用。
3. `platform_admin` 虽存在于角色枚举中，但 Day 10 不赋予跨租户读取权限；避免在 RBAC 前绕开隔离边界。
4. 对普通租户资源，跨租户访问必须返回 404 而非 403，防止借由资源存在性枚举其他租户数据。

### 3.1 `TenantScope` 设计

```python
@dataclass(frozen=True)
class TenantScope:
    tenant_id: str
    user_id: str
    role: str
```

- 只由已验证的 `User` 创建，禁止由请求 DTO、path/query 参数创建。
- `tenant_id` 是 Repository 查询必需条件；scope 缺失应在进入数据库查询前抛出 `UnauthorizedException`。
- `role` 仅为后续 RBAC 预留，本 Day 不据此放宽任意租户过滤。

### 3.2 资源查询规则

| 场景 | 行为 | 对外结果 |
|------|------|----------|
| 未认证或 ContextVar 缺失 | 不执行查询 | 401 / `40100` |
| 本租户资源存在 | 返回资源 | 200 / `code=0` |
| 资源不存在 | 不返回数据 | 404 / `40400` |
| 他租户资源 ID | 查询中因 tenant filter 无结果 | 404 / `40400` |
| 租户已禁用 | 已由 `get_current_user()` 拦截 | 401 / `40100` |

---

## 4. 接口契约

### `GET /api/v1/tenants/current`

请求头：

```http
Authorization: Bearer <access-token>
```

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "default-tenant-id",
    "name": "Acme Demo",
    "slug": "acme-demo",
    "status": "active"
  }
}
```

约束：

- 不接收 `tenant_id`，不允许通过 query/path/body 指定目标租户。
- 返回值只能来自 `current_user.tenant_id` 对应的数据库记录。
- 缺少、过期、Refresh 类型或跨租户伪造的 Access Token 均返回 401。

---

## 5. 逐文件实现规格

| 文件 | 改动要求 |
|------|----------|
| `backend/app/core/tenant_scope.py`（新增） | 定义冻结 `TenantScope`、`scope_from_user()` 和 `get_required_tenant_scope()`；中文职责注释，缺失上下文时抛 `UnauthorizedException`。 |
| `backend/app/repositories/base.py`（新增） | 定义 `TenantScopedRepository`：构造接收 `AsyncSession + TenantScope`；提供 `get_by_id()`，所有子类按 `model.id == resource_id AND model.tenant_id == scope.tenant_id` 查询。不得提供无 scope 的通用查询。 |
| `backend/app/repositories/tenant_repo.py`（新增） | 定义 `get_by_id_in_scope(tenant_id)`；即使传入 ID 也必须同时匹配 scope tenant_id 和 `Tenant.status == active`。 |
| `backend/app/services/tenant_service.py`（新增） | 定义 `get_current_tenant(current_user)`，从 User 创建 scope 后调用 Repository；无结果抛 `NotFoundException`。 |
| `backend/app/schemas/tenant.py`（新增） | 定义 `CurrentTenantResponse`：`id`、`name`、`slug`、`status`，不暴露内部统计或其他租户信息。 |
| `backend/app/api/v1/tenants.py`（新增） | 定义 `GET /current`；注入 `get_current_user`、`get_db`，只调用 Service，返回 `ApiResponse[CurrentTenantResponse]`。 |
| `backend/app/api/v1/router.py` | 挂载 tenants router，最终路径固定为 `/api/v1/tenants/current`。 |
| `backend/tests/test_tenant_scope.py`（新增） | 以可控 Session/Repository Fake 覆盖 scope 创建、scope 缺失、SQL 条件和跨租户无结果。 |
| `backend/tests/test_api_contract.py` | 覆盖 `/tenants/current` 的 200、401 与统一 envelope，不依赖开发数据库。 |
| `docs/api/tenants.md` | 将“当前租户信息”标记为已实现；其他租户管理 CRUD 仍标记为规划中，注明角色权限留待 Day 12+。 |

---

## 6. 实施顺序

1. 新建 `TenantScope` 与 Repository 基类，并为 scope 缺失、跨租户查询写纯单测。
2. 新建 Tenant Repository / Service / Schema，严格按 Service → Repository 分层。
3. 新增并挂载 `/tenants/current`，补 API 契约测试。
4. 运行质量门禁与本地双租户冒烟：创建第二租户/用户，用两组 token 分别读取 current，验证无法通过任意输入切换租户。
5. 通过后回写本 spec 的实现完成记录。

---

## 7. 测试与验证标准

```bash
cd backend
poetry run alembic upgrade head
poetry run ruff check app scripts tests
poetry run black --check app scripts tests
poetry run mypy app --ignore-missing-imports
poetry run pytest -q
```

至少覆盖：

1. `scope_from_user()` 只取 User 的 `id`、`tenant_id`、`role`，不接受前端 tenant 参数。
2. ContextVar 缺少 tenant scope 时不查询数据库，返回 40100。
3. `TenantScopedRepository.get_by_id()` 的查询始终附带 `tenant_id == scope.tenant_id`。
4. 传入他租户资源 ID 时结果为空并映射为 40400，不泄露资源存在。
5. `/api/v1/tenants/current` 对合法 Access Token 返回当前租户；无 Token 或 Refresh Token 返回 401。
6. 两个租户分别登录后，接口仅返回各自的 `id/name/slug`。

手动冒烟：使用默认管理员登录后访问 `/tenants/current`；尝试添加 `?tenant_id=<其他租户>` 或伪造 body，结果必须不改变返回租户。

---

## 8. Checkpoint / 执行前确认

- **当前理解**：Day 10 的交付不是“多一个租户接口”，而是建立后续所有租户数据访问必须复用的可信 scope 与 Repository 约束。
- **核心目标**：让遗漏 `tenant_id` 成为更难发生、可测试、可审查的错误，而不是依赖开发者记忆。
- **主要风险**：为平台管理员过早放开全局查询、把前端 tenant 参数混入授权路径、在无业务 CRUD 时把抽象做得过度复杂。
- **验证方式**：SQL/Repository 单测、API 契约测试、双租户 PostgreSQL 冒烟验证。
- **Execution Approval**：`Approved`（2026-07-17，用户已授权开始 Day 10 开发）。

---

## 9. 实现完成记录

> Day 10 全部需求开发完毕并验证通过后，按 CLAUDE.md §17 回写实际产出、验证结果与偏差。

### 完成时间

2026-07-17

### 实际产出文件

| 文件 | 说明 |
|------|------|
| `backend/app/core/tenant_scope.py` | 定义不可变 TenantScope，并校验 ContextVar 与已认证用户一致。 |
| `backend/app/repositories/base.py` | 提供后续业务 Repository 复用的 `id + tenant_id` 强制查询构造。 |
| `backend/app/repositories/tenant_repo.py` | 仅按当前 scope 读取活跃租户。 |
| `backend/app/services/tenant_service.py` | 编排可信 scope 与当前租户查询，隐藏无权资源。 |
| `backend/app/schemas/tenant.py` | 定义当前租户的最小公开响应 DTO。 |
| `backend/app/api/v1/tenants.py`、`router.py` | 新增并挂载 `GET /api/v1/tenants/current`。 |
| `backend/tests/test_tenant_scope.py` | 覆盖 scope 来源、ContextVar 缺失与 Repository tenant 条件。 |
| `backend/tests/test_api_contract.py` | 覆盖当前租户接口不会被 query 中伪造 tenant_id 覆盖。 |
| `docs/api/tenants.md` | 标注当前接口已实现，以及平台级 CRUD/RBAC 的后续边界。 |

### 验证结果

- ✅ `poetry run ruff check app scripts tests` → All checks passed。
- ✅ `poetry run black --check app scripts tests` → 54 个文件均无需格式化。
- ✅ `poetry run mypy app --ignore-missing-imports` → 53 个源文件无类型错误。
- ✅ `poetry run pytest -q` → 12 passed。
- ✅ 本地登录后调用 `GET /api/v1/tenants/current?tenant_id=forged-tenant-id` → HTTP 200，仍只返回 `default-tenant-id / acme-demo`。

### 验证结果

1. **最小闭环范围**：当前仅实现 `GET /tenants/current` 与通用 Repository 约束，不提前实现平台租户 CRUD 或跨租户管理员分支；这部分按课程规划留给 Day 12+ 的 RBAC。
2. **404 映射预留**：`TenantScopedRepository` 对他租户资源返回 `None`；具体业务 Service 在 Day 11 的资源 CRUD 中统一映射为 `NotFoundException`，当前租户接口不会接受任意资源 ID。

### 与 Spec 的偏差

待填写

### Resume / Handoff

- 当前状态：Day 10 已实现并完成本地验证。
- 下一步唯一动作：Day 11 将把 TenantScopedRepository 应用到知识库/文档等首个业务 CRUD。
