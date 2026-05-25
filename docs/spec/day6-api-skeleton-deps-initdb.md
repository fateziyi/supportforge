# Day 6 Spec：API 路由骨架 + 依赖注入 + 初始数据脚本

> 目标：在 Day 5 已完成全部 9 张核心业务表建模与迁移的基础上，为后端补齐**最小可运行的 API 骨架层**：让认证入口、路由组织、Schema 定义、初始化脚本都具备基础形态，从“只有模型”进化到“有接口边界、有初始化能力、有后续 Week 2 扩展入口”的状态。

---

## 1. Day 6 要解决什么问题

Day 5 之后，数据库结构已经齐了，但后端还缺少真正对外暴露的 API 骨架，因此还有 5 个核心缺口：

1. **还没有最小认证接口入口**：前端和联调方还没有 `/api/v1/auth/login` 这样的明确入口
2. **还没有请求/响应 Schema**：即使接口骨架存在，也缺少 Pydantic 模型来定义边界
3. **还没有初始化脚本**：数据库虽然有表，但没有默认租户、管理员账号，系统启动后无法演示
4. **路由聚合仍是“占位注释”状态**：Day 1 的 `router.py` 只挂了 `health`，还没有真正进入 API 骨架阶段
5. **依赖注入体系还不完整**：`get_db()` 已经真实可用，但 `get_current_user()` 仍是占位，缺少 Day 6 对“认证前骨架阶段”的明确约束

Day 6 就是解决这 5 个问题。

---

## 2. Day 6 目标产出

完成后新增 / 修改的核心文件如下：

```text
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                           # 保持 get_db 真实可用，明确 get_current_user 的 Day 6 边界
│   │   └── v1/
│   │       ├── router.py                     # 从“只挂 health”升级为“真实 API 骨架聚合器”
│   │       └── auth.py                       # 登录接口骨架（先 mock，不实现完整 JWT）
│   ├── schemas/
│   │   └── auth.py                           # LoginRequest / TokenResponse / CurrentUserResponse
│   └── db/
│       └── init_db.py                        # 初始化默认租户 + 默认管理员账号
└── scripts/
    └── init_demo_data.py                     # 可选：导入演示数据（Day 6 建议提供最小可用版）
```

> 说明：
> - Day 6 的核心不是“把认证做完”，而是把 **API 边界和初始化入口搭出来**
> - Day 6 允许登录接口先返回 mock token
> - JWT 的完整签发、解析、权限校验、刷新 token 等留到 Week 2

---

## 3. Day 6 实现边界

### Day 6 要做

| 模块 | 内容 |
|------|------|
| `app/api/v1/auth.py` | 提供最小登录接口骨架 |
| `app/schemas/auth.py` | 定义认证相关请求 / 响应模型 |
| `app/api/v1/router.py` | 从“注释占位”升级为真实 API 骨架聚合器 |
| `app/api/deps.py` | 保持 `get_db()` 真实可用，明确 `get_current_user()` 的 Day 6 骨架边界 |
| `app/db/init_db.py` | 初始化默认租户与管理员账号 |
| `scripts/init_demo_data.py` | 可选：导入 demo 数据，方便本地演示 |
| 验证 | `/docs` 能看到 auth 路由；执行 init_db 后数据库有默认数据 |

### Day 6 不做

| 不做 | 原因 |
|------|------|
| 完整 JWT 签发 / 刷新 / 黑名单 | Week 2 任务 |
| 完整用户认证链路（密码校验、用户锁定、token 过期） | Week 2 任务 |
| tenants / users / kb / documents / conversations / tickets 全部 CRUD API | Week 2 之后任务 |
| Service / Repository 正式实现 | Day 6 只做 API 骨架，不做完整业务层 |
| 真正的 demo 数据大批量导入 | Day 6 只需要最小演示数据 |
| Agent 节点调用、RAG 检索、工单自动流转 | Week 3/4/5 任务 |

---

## 4. 设计总原则（Day 6 必须遵守）

### 4.1 路由层只做“边界定义”，不做业务逻辑

根据 `CLAUDE.md` 的强制规范，Day 6 的路由层仍然必须遵守：
- 只做参数接收
- 只做响应返回
- 不在路由函数里写数据库 CRUD 细节
- 不在路由函数里写真正的认证逻辑

Day 6 的目标是：
- 把接口路径定下来
- 把请求 / 响应结构定下来
- 把后续 Week 2 要替换的 mock 边界留好

### 4.2 Mock 可以有，但必须可替换

Day 6 的 `auth.py` 可以先返回 mock token，但必须满足两个要求：
1. 接口路径、请求体、响应体尽量接近最终真实形态
2. mock 逻辑必须容易在 Week 2 被替换为真实 JWT 实现

### 4.3 初始化脚本优先追求“幂等”

`init_db.py` 最好满足：
- 重复执行不会反复插入同一批默认数据
- 默认租户已存在时跳过创建
- 默认管理员已存在时跳过创建

Day 6 不一定要做到 100% 完美幂等，但必须至少“重复执行不会把库搞乱”。

### 4.4 Schema 先覆盖认证最小闭环

Day 6 的 Pydantic Schema 不要求一次性把所有业务模块写全，至少先把认证最小闭环定义出来：
- 登录请求
- 登录响应
- 当前用户结构（可选，但推荐）

---

## 5. 逐文件实现规格

### 5.1 `backend/app/api/v1/auth.py`

**职责**：
- 定义认证相关的 API 路由骨架
- Day 6 先只要求最小登录入口
- 返回 mock token，为前端联调和 Swagger 演示提供入口

**建议表名 / 路由前缀**：

```python
router = APIRouter(prefix="/auth", tags=["auth"])
```

**Day 6 必须包含的接口**：

| 方法 | 路径 | 作用 |
|------|------|------|
| `POST` | `/api/v1/auth/login` | 登录接口骨架 |

**推荐接口形态**：

```python
@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    ...
```

**Day 6 行为要求**：
- 暂时不做真实密码校验
- mock 登录默认只支持初始化脚本创建出的默认管理员账号（如 `admin@acme.com`）
- 返回结构必须稳定，方便前端先接入

**推荐 mock 返回结构**：

```json
{
  "access_token": "mock-access-token",
  "refresh_token": "mock-refresh-token",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "admin-user-id",
    "tenant_id": "default-tenant-id",
    "email": "admin@acme.com",
    "role": "tenant_admin"
  }
}
```

**关键约束**：
- 路由层不直接查数据库，Day 6 允许先返回 mock
- 如果 Day 6 想做“从数据库查默认管理员是否存在”的轻量逻辑，也必须保持代码清晰，不把完整认证逻辑提前做进来
- Week 2 实现 JWT 时，应尽量保持请求/响应结构不变

---

### 5.2 `backend/app/schemas/auth.py`

**职责**：
- 定义认证相关请求和响应模型
- 让 Swagger 文档具备可读的接口结构
- 为后续 JWT 真正落地预留稳定数据契约

**Day 6 建议包含的模型**：

| 模型 | 职责 |
|------|------|
| `LoginRequest` | 登录请求体 |
| `CurrentUserResponse` | 当前用户信息 |
| `TokenResponse` | 登录成功后的响应 |

**推荐字段**：

#### `LoginRequest`

| 字段 | 类型 | 说明 |
|------|------|------|
| `email` | `EmailStr` | 登录邮箱 |
| `password` | `str` | 登录密码 |

#### `CurrentUserResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | 用户 ID |
| `tenant_id` | `str` | 所属租户 |
| `email` | `str` | 登录邮箱 |
| `role` | `str` | 角色 |

#### `TokenResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| `access_token` | `str` | 访问令牌 |
| `refresh_token` | `str` | 刷新令牌 |
| `token_type` | `str` | 通常为 `bearer` |
| `expires_in` | `int` | access token 过期秒数 |
| `user` | `CurrentUserResponse` | 当前登录用户信息 |

**关键约束**：
- Day 6 不要求引入复杂 schema 继承体系
- 先保证可读、清晰、Swagger 能看懂
- `email` 目标形态以 `EmailStr` 为准；如果 Day 6 实现时当前依赖暂不满足邮箱校验要求，可临时退化为 `str`，但 Week 2 应收敛回 `EmailStr`
- 字段命名尽量接近未来真实 JWT 接口，避免 Week 2 大改前端联调契约

---

### 5.3 `backend/app/api/v1/router.py`

**职责变化**：
- 从 Day 1 的“只挂 health”升级为真正的 v1 API 骨架聚合器
- Day 6 至少要真实挂载 `auth_router`

**Day 6 修改后建议结构**：

```python
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router)
```

**关键约束**：
- `/api/v1/health` 仍然保持不变
- `auth_router` 自己带 prefix=`/auth` 和 tags=`["auth"]`
- Day 6 只要求真实挂载 `health_router` + `auth_router`
- 其他模块（tenants / users / kb / documents / conversations / tickets / audit_logs）继续保留注释占位，不强制 Day 6 创建对应路由文件

---

### 5.4 `backend/app/api/deps.py`

**职责变化**：
- `get_db()` 已经是真实数据库依赖，Day 6 不要再改坏
- `get_current_user()` 仍然是占位，但要明确它和 Day 6 auth mock 的关系

**Day 6 的边界建议**：

- `get_db()`：继续从 `app.db.session` 转发，不动
- `get_current_user()`：保持占位即可，或者改成返回一个 mock 用户对象（两种都可以）

**推荐方案**：
保持 `get_current_user()` 为占位，不提前引入 mock 用户依赖。原因：
- Day 6 的目标是开放 auth 接口入口，不是完成鉴权体系
- 如果现在做 mock current user，Week 2 再切真实 JWT 时会多一层替换成本

**关键约束**：
- `deps.py` 里不写 JWT 解析逻辑
- `deps.py` 里不重复造 session
- `get_db()` 必须继续作为数据库依赖的唯一入口

---

### 5.5 `backend/app/db/init_db.py`

**职责**：
- 初始化默认租户
- 初始化默认管理员账号
- 为本地演示和 Day 6 验证提供基础数据

**Day 6 必须包含的能力**：

| 能力 | 说明 |
|------|------|
| 创建默认租户 | 如 `Acme Demo` |
| 创建默认管理员 | 如 `admin@acme.com` |
| 幂等执行 | 如果已存在则跳过 |
| 可独立运行 | 通过 `python -m app.db.init_db` 或脚本执行 |

**推荐默认数据**：

| 对象 | 推荐值 |
|------|--------|
| 默认租户 ID | `default-tenant-id`（或 UUID） |
| 默认租户名称 | `Acme Demo` |
| 管理员邮箱 | `admin@acme.com` |
| 管理员角色 | `tenant_admin` |
| 管理员初始密码 | `123456`（Day 6 可先写死并 hash；Week 2 再优化） |

**关键约束**：
- 即使 Day 6 还没做完整认证，也不能把明文密码直接存进 `password_hash`
- 建议至少先用一个临时 hash 值，或者写一个极简 hash 辅助函数
- `init_db.py` 允许直接使用数据库 session，但只允许承载“初始化专用的最小逻辑”
- 不要把它写成通用业务层；如果后续初始化逻辑变复杂，应在 Week 2/3 抽到 service / repository

**推荐执行方式**：

```bash
cd backend
poetry run python -m app.db.init_db
```

---

### 5.6 `scripts/init_demo_data.py`（可选但推荐）

**职责**：
- 在默认租户和管理员基础上，再补少量演示数据
- 方便 Day 6 / Day 7 本地联调演示

**Day 6 是否必须**：
- **可选但推荐**
- 不纳入 Day 6 必做 DoD
- 如果时间不够，可以跳过，并在 Day 6 完成记录中说明“本轮未实现，留到 Day 7 / Week 2”

**最小推荐内容**：
- 创建一个知识库
- 创建一条文档记录
- 可选：创建一条 conversation 与一条 ticket

**关键约束**：
- 不要把 demo 数据写太多
- 仍然尽量幂等
- 目标是“让 Swagger/数据库演示更完整”，不是做完整测试工厂

---

## 6. Day 6 最小接口与数据闭环

### 6.1 Day 6 闭环目标

```text
数据库已有 9 张核心表
  ↓
执行 init_db.py
  ↓
数据库出现默认租户 + 默认管理员
  ↓
启动 FastAPI
  ↓
Swagger 中出现 /api/v1/auth/login
  ↓
调用登录接口
  ↓
返回 mock token + 当前用户信息
```

### 6.2 Day 6 最小骨架图

```text
main.py
  └── include_router(api_router, prefix="/api/v1")
        ├── health_router
        └── auth_router

schemas/auth.py
  ├── LoginRequest
  ├── CurrentUserResponse
  └── TokenResponse

api/deps.py
  ├── get_db()            # 已真实可用
  └── get_current_user()  # 仍为 Week 2 占位

db/init_db.py
  ├── create_default_tenant()
  └── create_default_admin_user()
```

---

## 7. 验证标准

### 7.1 路由文档验证

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

预期：
- `/docs` 可访问
- Swagger 文档中能看到：
  - `GET /api/v1/health`
  - `POST /api/v1/auth/login`

---

### 7.2 初始化脚本验证

```bash
cd backend
poetry run python -m app.db.init_db
```

预期：
- 默认租户被创建（若已存在则跳过）
- 默认管理员被创建（若已存在则跳过）
- 终端输出清晰提示：created / skipped

---

### 7.3 数据库验证

```bash
podman exec supportforge-postgres psql -U supportforge -c "select id, name, status from tenants;"
podman exec supportforge-postgres psql -U supportforge -c "select email, role, status from users;"
```

预期：
- `tenants` 表中存在默认租户
- `users` 表中存在默认管理员账号

---

### 7.4 登录接口验证

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@acme.com","password":"123456"}'
```

预期：
- 返回 200
- 返回中包含：
  - `access_token`
  - `refresh_token`
  - `token_type`
  - `expires_in`
  - `user`

---

### 7.5 Lint 验证

```bash
cd backend
poetry run ruff check app/
poetry run black --check app/
```

预期：全部通过。

---

## 8. 与后续开发的衔接关系

Day 6 完成后，以下能力就具备前提了：

| 后续阶段 | 依赖 Day 6 的内容 |
|----------|------------------|
| Week 2 JWT 真正落地 | 直接替换 `auth.py` 的 mock 登录逻辑 |
| Week 2 当前用户依赖 | 在 `deps.py` 中把占位实现替换为真实 JWT 解析 |
| 前端联调 | `/api/v1/auth/login` 已有稳定路径和响应结构 |
| Day 7 集成验证 | init_db + auth 路由 + Swagger 已形成最小演示闭环 |
| 后续业务 API | 可沿用 Day 6 的路由组织方式继续扩展 tenants/users/kb/documents 等模块 |

---

## 9. Day 6 完成标准（DoD）

完成 Day 6，至少要满足以下检查项：

- [ ] `app/api/v1/auth.py` 已创建
- [ ] `app/schemas/auth.py` 已创建
- [ ] `app/db/init_db.py` 已创建
- [ ] `scripts/init_demo_data.py` 已创建，或已在本轮明确标注为“可选并跳过”
- [ ] `api/v1/router.py` 已真实挂载 `auth_router`
- [ ] `/docs` 中能看到 `POST /api/v1/auth/login`
- [ ] `LoginRequest` / `TokenResponse` Schema 已定义清楚
- [ ] `init_db.py` 能创建默认租户和管理员账号
- [ ] 初始化脚本重复执行不会反复插入脏数据
- [ ] 登录接口能返回稳定的 mock token 结构
- [ ] `ruff` / `black` 通过
- [ ] 不提前把完整 JWT 鉴权逻辑写进 Day 6

---

## 10. 常见坑与排错建议

### 10.1 把 Day 6 做成了“半个 Week 2”

**常见问题**：
- 一开始就写 JWT 签发、解析、权限校验、刷新 token
- 导致 Day 6 任务膨胀，返工风险上升

**建议**：
- Day 6 只做 mock 登录入口 + Schema + 初始化脚本
- 真正认证链路留到 Week 2

---

### 10.2 初始化脚本重复执行插入脏数据

**常见问题**：
- 每次执行都插入一个新租户 / 新管理员

**建议**：
- 按 `tenant.name` 或固定 `tenant.id` 先查后插
- 按管理员邮箱先查后插

---

### 10.3 把明文密码直接写进 `password_hash`

**常见问题**：
- Day 6 为了省事，直接把 `123456` 存入 `password_hash`

**建议**：
- 至少写一个临时 hash 值
- 或者实现一个极简 hash 辅助函数
- 即使是 demo 数据，也不要破坏字段语义

---

### 10.4 路由层写了太多逻辑

**常见问题**：
- 在 `auth.py` 的登录函数里直接写完整数据库查询、密码比较、token 生成

**建议**：
- Day 6 路由层只返回 mock
- 如果一定要查默认用户是否存在，也保持逻辑极简

---

### 10.5 Swagger 文档结构不稳定

**常见问题**：
- Day 6 的响应结构和 Week 2 真实接口相差太大

**建议**：
- 让 mock 返回结构尽量接近未来真实结构
- 后续 Week 2 尽量只替换内部逻辑，不改外部契约

---

## 11. 实施顺序建议

Day 6 推荐按这个顺序实现：

1. 先写 `schemas/auth.py`
2. 再写 `api/v1/auth.py`
3. 再更新 `api/v1/router.py` 挂载 `auth_router`
4. 再补 `db/init_db.py`
5. 最后视时间决定是否写 `scripts/init_demo_data.py`
6. 按验证清单逐项验证

这样做的好处是：
- 先把请求 / 响应契约定下来
- 再把接口路径接起来
- 最后补初始化数据，避免接口写好后没有可演示数据

---

## 12. 实现完成记录

> 本章节记录 Day 6 spec 实际完成情况，包含产出文件、验证结果、与 spec 的偏差说明。

### 完成时间

2026-05-25

### 实际产出文件

| 文件 | 说明 |
|------|------|
| `backend/app/schemas/auth.py` | `LoginRequest`(EmailStr) / `CurrentUserResponse`(id, tenant_id, email, role) / `TokenResponse`(access_token, refresh_token, token_type, expires_in, user) |
| `backend/app/schemas/__init__.py` | 补充导入 3 个 auth Schema（redundant alias 模式） |
| `backend/app/api/v1/auth.py` | Mock 登录接口 `POST /api/v1/auth/login`，只支持默认管理员 `admin@acme.com`，返回 mock token |
| `backend/app/api/v1/router.py` | 从只挂 health → 挂 health + auth_router |
| `backend/app/db/init_db.py` | 初始化默认租户(Acme Demo) + 默认管理员(admin@acme.com)，幂等执行，密码用临时 sha256 哈希 |
| `backend/scripts/__init__.py` | scripts 包初始化 |
| `backend/scripts/init_demo_data.py` | 可选 demo 数据：知识库(Acme Help Center) + 文档(FAQ.md) + 对话 + 工单，全部幂等 |
| `backend/pyproject.toml` | 新增 `email-validator` 依赖 |

### 验证结果

- ✅ `ruff check app/ scripts/` → All checks passed!
- ✅ `black --check app/ scripts/` → 39 files would be left unchanged
- ✅ `/docs` Swagger 显示 `GET /api/v1/health` + `POST /api/v1/auth/login`
- ✅ `poetry run python -m app.db.init_db` → 创建默认租户 + 管理员，重复执行幂等跳过
- ✅ `poetry run python -m scripts.init_demo_data` → 创建知识库 + 文档 + 对话 + 工单，重复执行幂等跳过
- ✅ `curl POST /api/v1/auth/login {"email":"admin@acme.com","password":"123456"}` → 200，返回 mock token + user 信息
- ✅ `curl POST /api/v1/auth/login {"email":"other@acme.com","password":"123456"}` → 401，仅支持默认管理员
- ✅ `curl POST /api/v1/auth/login {"email":"not-an-email","password":"123456"}` → 422，EmailStr 校验生效
- ✅ PostgreSQL `\dt` → 10 张表（9 业务 + alembic_version）， tenants/users/knowledge_bases/documents 各有演示数据行

### 与 Spec 的偏差

1. **密码哈希决策收敛为 argon2**：spec 原文多处提到"bcrypt 或 argon2"，经用户确认后统一为 argon2（比 bcrypt 更抗 GPU/ASIC 暴力破解），相关注释已更新

2. **Demo 数据脚本补全 conversation + ticket**：spec §5.6 原文只明确要求知识库 + 文档，conversation 和 ticket 标注为"可选"，实作时补上了这两项，幂等策略使用固定 ID（因为 conversation/ticket 没有天然唯一标识字段）

3. **EmailStr 使用 `email-validator` 依赖**：spec 原文允许"如果依赖不满足可退化为 str"，实作时直接添加了 `email-validator` 依赖，使用完整 `EmailStr` 类型

4. **Demo 文档的 Document.title 改为 Document.filename**：实作过程中发现 Document 模型没有 `title` 字段（实际是 `filename`），已修正