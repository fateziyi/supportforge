# Day 4 Spec：核心模型（Part 1）— 租户 + 用户 + 知识库 + 文档

> 目标：在 Day 3 已完成数据库连接、ORM 基类、Alembic 初始化的基础上，完成第一批 4 张核心业务表的 ORM 模型设计与迁移生成，让数据库具备最小业务骨架，并为 Week 2 登录认证、知识库管理、文档管理打下数据结构基础。

---

## 1. Day 4 要解决什么问题

Day 3 已经把数据库基础设施搭好了，但当前项目还缺少真正的业务表，因此有 4 个核心缺口：

1. **数据库里还没有核心业务实体表**：目前只有 `alembic_version` 表
2. **认证系统没有用户与租户载体**：Week 2 的 JWT / 登录认证需要 `users` 和 `tenants` 表支撑
3. **知识库与文档管理没有数据落点**：Week 3 的 RAG 文档入库要依赖 `knowledge_bases` 和 `documents` 表
4. **多租户隔离还没有落到模型层**：租户边界必须体现在表结构设计中，而不是只停留在文档约束里

Day 4 就是解决这 4 个问题。

---

## 2. Day 4 目标产出

完成后新增 / 修改的核心文件如下：

```text
backend/app/
├── models/
│   ├── __init__.py                 # 导入 Day 4 的全部模型，供 Alembic 识别
│   ├── tenant.py                   # 租户表模型
│   ├── user.py                     # 用户表模型
│   ├── knowledge_base.py           # 知识库表模型
│   └── document.py                 # 文档表模型
└── db/
    └── migrations/
        └── versions/
            └── <revision>_add_tenant_user_kb_doc_tables.py
```

> 说明：
> - Day 4 只覆盖第一批 4 张表：`tenants`、`users`、`knowledge_bases`、`documents`
> - Day 4 完成后，数据库中应能看到这 4 张表 + `alembic_version`
> - Day 4 不要求写 repository / service / API，只做模型与迁移

---

## 3. Day 4 实现边界

### Day 4 要做

| 模块 | 内容 |
|------|------|
| `models/tenant.py` | 定义租户表 |
| `models/user.py` | 定义用户表，关联租户 |
| `models/knowledge_base.py` | 定义知识库表，归属租户 |
| `models/document.py` | 定义文档表，归属租户与知识库 |
| `models/__init__.py` | 导入 Day 4 全部模型，让 Alembic autogenerate 能识别 |
| Alembic 迁移 | 生成并执行第一批业务表迁移 |
| 验证 | 数据库里能看到 4 张新表，字段和外键符合预期 |

### Day 4 不做

| 不做 | 原因 |
|------|------|
| 对话、工单、审计、Agent 执行记录等剩余 5 张表 | Day 5 任务 |
| 初始化默认租户和管理员账号 | Day 6 的 `init_db.py` 任务 |
| Repository / CRUD | 依赖模型完成后再做 |
| Pydantic Schema | Day 6/Week 2 再逐步补 |
| API 路由 | Day 6 任务 |
| JWT / 密码校验逻辑 | Week 2 任务 |
| 文档解析、向量入库、RAG 逻辑 | Week 3 任务 |

---

## 4. 设计总原则（Day 4 必须遵守）

### 4.1 多租户优先原则

Day 4 的 4 张表里，除了平台级公共信息之外，所有业务数据必须天然具备租户隔离能力：

| 表 | 是否必须有 `tenant_id` | 原因 |
|----|------------------------|------|
| `tenants` | 否 | 自己就是租户表 |
| `users` | 是 | 用户归属于一个租户 |
| `knowledge_bases` | 是 | 知识库归属于一个租户 |
| `documents` | 是 | 文档归属于一个租户 |

### 4.2 先清晰、后丰富

Day 4 只追求：
- 字段清晰
- 关系正确
- 能生成迁移
- 能面试讲明白

不追求：
- 一次性把所有边缘字段都补齐
- 提前做复杂索引优化
- 提前做状态流转逻辑

### 4.3 统一风格

所有模型必须遵循 Day 3 已建立的约束：
- 继承 `Base`
- 需要时间戳的表继承 `TimestampMixin`
- 使用 SQLAlchemy 2.0 风格：`Mapped[...]` + `mapped_column(...)`
- 优先写清晰中文注释，方便你后续理解和面试表述

---

## 5. 逐文件实现规格

### 5.1 `backend/app/models/tenant.py`

**职责**：
- 定义租户表，作为多租户 SaaS 的顶层主体
- 后续所有租户隔离数据都将归属于某个 tenant

**建议表名**：

```python
__tablename__ = "tenants"
```

**Day 4 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` 或 `UUID` | 租户唯一标识 |
| `name` | `String(100)` | 租户名称，建议唯一 |
| `status` | `String(20)` | 租户状态，如 `active` / `disabled` |
| `created_at` | 继承自 `TimestampMixin` | 创建时间 |
| `updated_at` | 继承自 `TimestampMixin` | 更新时间 |

**推荐实现方向**：

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
```

**关键约束**：
- `name` 建议加唯一约束，避免重复创建同名租户
- `status` 先用字符串，不急着上 Enum，减少 Day 4 的复杂度
- Day 4 不需要加 `settings_json`、`plan_type` 等扩展字段，保持最小可用

---

### 5.2 `backend/app/models/user.py`

**职责**：
- 定义用户表
- 为 Week 2 登录认证、RBAC、租户内用户管理提供数据基础

**建议表名**：

```python
__tablename__ = "users"
```

**Day 4 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | 用户 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 ID |
| `username` | `String(50)` | 用户名 |
| `email` | `String(120)` | 登录邮箱 |
| `password_hash` | `String(255)` | 加密后的密码 |
| `role` | `String(30)` | 角色，可选值必须与 CLAUDE.md §7 一致：`platform_admin` / `tenant_admin` / `support_agent` / `auditor` |
| `status` | `String(20)` | 用户状态，如 `active` / `disabled` |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳 |

**推荐关系**：
- `tenant`：多对一，用户属于一个租户

**推荐实现方向**：

```python
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # role 可选值必须与 CLAUDE.md §7 一致：platform_admin / tenant_admin / support_agent / auditor
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    tenant = relationship("Tenant")
```

**关键约束**：
- `email` 是否全局唯一，Day 4 先不强行拍板；更推荐做成**租户内唯一**，但这需要联合唯一约束，Day 4 可以只在 spec 中说明，实作时根据你理解决定
- `role` 先用字符串，但可选值必须与 CLAUDE.md §7 的 RBAC 角色规范完全一致：`platform_admin`、`tenant_admin`、`support_agent`、`auditor`
- `password_hash` 存储加密后的密码，绝不能叫 `password`
- `tenant_id` 必须有索引，后续所有按租户查询都会频繁使用

**Day 4 唯一约束决策**：
- `(tenant_id, email)` 联合唯一 → **Day 4 必加**，这是多租户 SaaS 的基本约束，同一租户内不允许注册重复邮箱
- `(tenant_id, username)` 联合唯一 → **Day 4 必加**，理由同上
- 实现方式：在 `User` 模型上使用 `__table_args__ = (UniqueConstraint(...),)

---

### 5.3 `backend/app/models/knowledge_base.py`

**职责**：
- 定义知识库表
- 作为文档归属与 RAG 检索的逻辑容器

**建议表名**：

```python
__tablename__ = "knowledge_bases"
```

**Day 4 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | 知识库 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 |
| `name` | `String(100)` | 知识库名称 |
| `description` | `Text` 或 `String(500)` | 描述 |
| `status` | `String(20)` | 状态，如 `active` / `archived` |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳 |

**推荐关系**：
- `tenant`：多对一，知识库属于一个租户
- `documents`：一对多，一个知识库下有多个文档

**关键约束**：
- `tenant_id` 必须有索引
- `(tenant_id, name)` 联合唯一 → **Day 4 必加**，同一租户内不允许创建同名知识库
- 实现方式：在 `KnowledgeBase` 模型上使用 `__table_args__ = (UniqueConstraint(...),)`
- Day 4 不必增加文档统计字段（如 `document_count`），避免冗余状态

---

### 5.4 `backend/app/models/document.py`

**职责**：
- 定义文档表
- 为 Week 3 的文档上传、解析、切片、向量入库提供持久化基础

**建议表名**：

```python
__tablename__ = "documents"
```

**Day 4 必须包含的字段**：

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | `String(36)` | 文档 ID |
| `tenant_id` | `ForeignKey("tenants.id")` | 所属租户 |
| `knowledge_base_id` | `ForeignKey("knowledge_bases.id")` | 所属知识库 |
| `filename` | `String(255)` | 原始文件名 |
| `file_path` | `String(500)` | 文件存储路径 |
| `status` | `String(30)` | 状态，如 `uploaded` / `parsing` / `ready` / `failed` |
| `mime_type` | `String(100)` | 文件 MIME 类型（Day 4 必加，Week 3 文档解析需根据类型决定解析策略） |
| `created_at` / `updated_at` | 继承自 `TimestampMixin` | 时间戳 |

**推荐关系**：
- `tenant`：多对一
- `knowledge_base`：多对一

**关键约束**：
- `tenant_id` 和 `knowledge_base_id` 都应建索引
- `status` 先用字符串，后续再考虑 Enum
- Day 4 不必加入 chunk_count、token_count、embedding_status 等二阶字段

---

### 5.5 `backend/app/models/__init__.py`

**职责变化**：
- 从 Day 1 的占位注释升级为真实模型导入入口
- 让 `app.db.migrations.env.py` 通过 `import app.models` 时，能把全部模型加载到 `Base.metadata`

**Day 4 需要导入的内容**：

```python
from app.models.tenant import Tenant
from app.models.user import User
from app.models.knowledge_base import KnowledgeBase
from app.models.document import Document
```

**关键约束**：
- 这里的导入顺序尽量清晰：先 `Tenant`，再 `User`，再 `KnowledgeBase`，最后 `Document`
- 不要在 `__init__.py` 里写业务逻辑
- 后续 Day 5 继续在这里补充新增模型导入

---

### 5.6 Alembic 迁移生成

**职责**：
- 基于 Day 4 的模型定义自动生成第一批业务表迁移脚本
- 把模型定义真正落到 PostgreSQL 数据库中

**推荐命令**：

```bash
cd backend
poetry run alembic revision --autogenerate -m "add tenant user kb doc tables"
poetry run alembic upgrade head
```

**预期结果**：
- `app/db/migrations/versions/` 下出现新的 revision 文件
- 升级成功后，数据库里出现：
  - `tenants`
  - `users`
  - `knowledge_bases`
  - `documents`
  - `alembic_version`

**关键约束**：
- migration message 建议简洁明确，方便后续回看
- 如果 autogenerate 没发现新表，第一时间检查 `models/__init__.py` 是否正确导入
- 迁移脚本生成后建议人工过一遍，确认字段、外键、索引符合预期

---

## 6. 字段与关系建议总表

### 6.1 Day 4 四张表概览

| 表名 | 主键 | 关键外键 | 主要作用 |
|------|------|----------|----------|
| `tenants` | `id` | 无 | 多租户顶层实体 |
| `users` | `id` | `tenant_id -> tenants.id` | 用户与 RBAC 基础 |
| `knowledge_bases` | `id` | `tenant_id -> tenants.id` | 知识库容器 |
| `documents` | `id` | `tenant_id -> tenants.id`, `knowledge_base_id -> knowledge_bases.id` | 文档上传与解析基础 |

### 6.2 Day 4 建议的最小关系图

```text
Tenant
  ├── User (1:N)
  ├── KnowledgeBase (1:N)
  └── Document (1:N)

KnowledgeBase
  └── Document (1:N)
```

---

## 7. 验证标准

### 7.1 模型导入验证

```bash
cd backend
poetry run python -c "from app.models import Tenant, User, KnowledgeBase, Document; print(Tenant, User, KnowledgeBase, Document)"
```

预期：
- 4 个模型都能成功导入
- 不出现循环导入错误、relationship 解析错误、字段定义错误

---

### 7.2 Metadata 识别验证

```bash
cd backend
poetry run python -c "from app.db.base import Base; import app.models; print(Base.metadata.tables.keys())"
```

预期：
- 输出中至少包含：
  - `tenants`
  - `users`
  - `knowledge_bases`
  - `documents`

---

### 7.3 迁移生成验证

```bash
cd backend
poetry run alembic revision --autogenerate -m "add tenant user kb doc tables"
```

预期：
- 成功生成迁移脚本
- 迁移脚本中包含 4 张表的 `create_table(...)`
- 包含合理的外键和索引定义

---

### 7.4 数据库落表验证

```bash
cd backend
poetry run alembic upgrade head
podman exec supportforge-postgres psql -U supportforge -c "\dt"
```

预期：
- PostgreSQL 中看到：
  - `alembic_version`
  - `tenants`
  - `users`
  - `knowledge_bases`
  - `documents`

---

## 8. 与后续开发的衔接关系

Day 4 完成后，以下能力就具备前提了：

| 后续阶段 | 依赖 Day 4 的内容 |
|----------|------------------|
| Day 5 模型扩展 | 在现有 4 张表基础上追加对话、工单、审计等表 |
| Week 2 登录认证 | `users` + `tenants` 提供登录、租户解析、角色校验的数据基础 |
| Week 3 知识库与文档管理 | `knowledge_bases` + `documents` 作为业务数据基础 |
| Repository 层 | 可以基于这些模型写 CRUD 查询 |
| init_db 脚本 | 可以创建默认租户和管理员账号 |

---

## 9. Day 4 完成标准（DoD）

完成 Day 4，至少要满足以下检查项：

- [ ] `models/tenant.py` 已创建
- [ ] `models/user.py` 已创建
- [ ] `models/knowledge_base.py` 已创建
- [ ] `models/document.py` 已创建
- [ ] 4 个模型都继承了 `Base`
- [ ] 需要时间戳的模型都继承了 `TimestampMixin`
- [ ] `users`、`knowledge_bases`、`documents` 都有 `tenant_id`
- [ ] `documents` 有 `knowledge_base_id`
- [ ] `models/__init__.py` 已正确导入 Day 4 全部模型
- [ ] `Base.metadata.tables.keys()` 能看到 4 张表
- [ ] Alembic autogenerate 能生成迁移脚本
- [ ] `alembic upgrade head` 后数据库里能看到 4 张新表
- [ ] 字段命名、角色命名、多租户约束与 CLAUDE.md 保持一致
- [ ] 代码注释足够清楚，方便你后续面试讲解

---

## 10. 常见坑与排错建议

### 10.1 `alembic revision --autogenerate` 没有发现新表

**常见原因**：
- `app/models/__init__.py` 没有导入新模型
- `env.py` 没有 `import app.models`
- 模型没有继承 `Base`

**排查顺序**：
1. `poetry run python -c "import app.models"`
2. `poetry run python -c "from app.db.base import Base; import app.models; print(Base.metadata.tables.keys())"`
3. 再执行 `alembic revision --autogenerate`

---

### 10.2 relationship 报循环导入或类名找不到

**原因**：
- 在模型文件顶部直接导入了彼此，形成循环引用

**建议**：
- `relationship()` 里优先用字符串类名，如 `relationship("Tenant")`
- 不在模型文件之间做不必要的互相 import

---

### 10.3 外键写错表名

**典型错误**：
- 把 `knowledge_base` 写成 `knowledge_bases`
- 把 `tenant` 写成 `tenants`

**建议**：
- 先明确每个模型的 `__tablename__`
- `ForeignKey("表名.字段名")` 必须和真实表名一致

---

### 10.4 字段过度设计导致 Day 4 过重

**表现**：
- 一口气加入太多统计字段、业务状态字段、JSON 配置字段
- 导致迁移复杂、后续还要频繁回改

**建议**：
- Day 4 先做“最小可用模型”
- 扩展字段宁可 Day 5 / Week 2 再补，也不要今天一次性堆满

---

### 10.5 唯一约束设计过早拍死

**典型问题**：
- `email` 到底全局唯一还是租户内唯一？
- `知识库名称` 到底是否允许租户间重名？

**建议**：
- 优先遵循业务直觉：
  - 租户间允许重名
  - 租户内不允许重复
- 如果当前拿不准，Spec 可以先标“推荐”，实现时采用最稳妥的最小约束方案

---

## 11. 实施顺序建议

Day 4 推荐按这个顺序实现：

1. 先写 `tenant.py`
2. 再写 `user.py`
3. 再写 `knowledge_base.py`
4. 最后写 `document.py`
5. 更新 `models/__init__.py`
6. 验证 `Base.metadata.tables.keys()`
7. 生成 Alembic 迁移脚本
8. 执行 `upgrade head`
9. 在 PostgreSQL 中确认 4 张表都存在

这样做的好处是：
- 先从根实体 `Tenant` 开始，关系最清晰
- 再逐步向下添加依赖它的用户、知识库、文档
- 最后统一交给 Alembic 生成迁移，减少反复回滚

---

## 11. 实现完成记录

> 本章节记录 Day 4 spec 实际完成情况，包含产出文件、验证结果、与 spec 的偏差说明。

### 完成时间

2026-05-21

### 实际产出文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/tenant.py` | `Tenant(Base, TimestampMixin)` — id / name(unique) / status |
| `backend/app/models/user.py` | `User(Base, TimestampMixin)` — id / tenant_id(FK) / username / email / password_hash / role / status + 2 个联合唯一约束 |
| `backend/app/models/knowledge_base.py` | `KnowledgeBase(Base, TimestampMixin)` — id / tenant_id(FK) / name / description / status + (tenant_id, name) 联合唯一 |
| `backend/app/models/document.py` | `Document(Base, TimestampMixin)` — id / tenant_id(FK) / knowledge_base_id(FK) / filename / file_path / mime_type / status |
| `backend/app/models/__init__.py` | 导入全部 4 个模型（redundant alias 模式满足 ruff F401） |
| `backend/app/db/migrations/versions/f6c7458fff25_add_tenant_user_kb_doc_tables.py` | Alembic 迁移脚本，含 4 张表建表 + 外键 + 索引 + 联合唯一 |

### 验证结果

- ✅ `from app.models import Tenant, User, KnowledgeBase, Document` → 4 个模型导入成功
- ✅ `Base.metadata.tables.keys()` → `['documents', 'knowledge_bases', 'tenants', 'users']`
- ✅ `alembic revision --autogenerate -m "add tenant user kb doc tables"` → 成功生成 revision `f6c7458fff25`
- ✅ 迁移脚本包含：4 张 `create_table` + 3 个联合唯一约束 + 5 个索引 + 2 个外键
- ✅ `alembic upgrade head` → Running upgrade → f6c7458fff25
- ✅ `\dt` 显示 5 张表：`alembic_version` + `tenants` + `users` + `knowledge_bases` + `documents`
- ✅ `poetry run uvicorn app.main:app` 启动正常，`/api/v1/health` 返回 200
- ✅ `ruff check app/` → All checks passed!
- ✅ `black --check app/` → 通过

### 与 Spec 的偏差

1. **`models/__init__.py` 导入方式**：Spec 写 `from app.models.tenant import Tenant`，实作改为 `from app.models.tenant import Tenant as Tenant`（redundant alias），以满足 ruff F401 规则。这是 `__init__.py` 集中导入场景下的标准做法

2. **`KnowledgeBase` 反向关系**：实作时加了 `documents = relationship("Document", back_populates="knowledge_base")`，Spec 只说"推荐关系"没有明确写，但实作选择了完整的双向 relationship

3. **`Document.mime_type` 字段**：Spec 审查后从"可选但推荐"改为"Day 4 必加"，实作确实加了 `mime_type: Mapped[str] = mapped_column(String(100), nullable=False)`
