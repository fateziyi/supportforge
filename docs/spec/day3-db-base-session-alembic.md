# Day 3 Spec：数据库连接 + ORM 基类 + Alembic 初始化

> 目标：在 Day 2 已具备配置、日志、异常处理能力的基础上，为后端补齐**数据库访问基础设施**，让项目具备真正可持续开发的数据层基座：能连接 PostgreSQL、能提供 `AsyncSession` 依赖、能初始化 Alembic 迁移框架，并为 Day 4/Day 5 的 ORM 模型开发做好准备。

---

## 1. Day 3 要解决什么问题

Day 1 让 FastAPI 跑起来了，Day 2 把工程化基础打好了，但当前后端仍然有 4 个核心缺口：

1. **还没有真正连接数据库**：`settings.database_url` 已存在，但没有 `engine` 和 `sessionmaker`
2. **API 层还拿不到数据库会话**：`api/deps.py` 里的 `get_db()` 仍然是占位实现
3. **还没有 ORM 基类**：Day 4/Day 5 写模型时，没有统一的 `Base`、时间戳字段、主键约定
4. **还没有迁移体系**：数据库表结构无法做版本管理，后续建表会越来越混乱

Day 3 就是解决这 4 个问题。

---

## 2. Day 3 目标产出

完成后新增 / 修改的核心文件如下：

```text
backend/
├── alembic.ini                         # Alembic 配置文件
├── app/
│   ├── main.py                         # 需要补充数据库生命周期接入（startup/shutdown）
│   ├── api/
│   │   └── deps.py                     # get_db() 从占位改成真实数据库依赖
│   └── db/
│       ├── __init__.py
│       ├── base.py                     # ORM 基类 + 公共 Mixin
│       ├── session.py                  # async engine + async_sessionmaker + get_db
│       └── migrations/
│           ├── env.py                  # Alembic 运行入口，绑定项目 metadata
│           ├── script.py.mako          # Alembic 模板（初始化生成）
│           └── versions/               # 迁移脚本目录（Day 3 可以为空）
└── pyproject.toml                      # 仅当 Alembic/SQLAlchemy 依赖缺失时才补，不重复改
```

> 说明：
> - Day 3 **不要求真正创建业务表**，因为业务表模型是 Day 4/Day 5 的任务
> - Day 3 至少要做到：`alembic upgrade head` 能正常执行，并在数据库里出现 `alembic_version` 表

---

## 3. Day 3 实现边界

### Day 3 要做

| 模块 | 内容 |
|------|------|
| `db/base.py` | 定义 `DeclarativeBase`，提供公共时间戳 Mixin |
| `db/session.py` | 创建异步 engine、`async_sessionmaker`、`get_db()` 依赖 |
| `api/deps.py` | 把 Day 1 的 `get_db()` 占位替换为真实依赖导出 |
| Alembic 初始化 | 创建 `alembic.ini`、`app/db/migrations/`、配置 `env.py` |
| `main.py` | 接入数据库生命周期（至少预留并实现基础 connect/dispose 管理） |
| 验证 | 能连接 PostgreSQL、Alembic 可运行、`get_db()` 可导入 |

### Day 3 不做

| 不做 | 原因 |
|------|------|
| 创建 `Tenant/User/KnowledgeBase/...` 等业务 ORM 模型 | Day 4 / Day 5 任务 |
| 生成业务表迁移脚本 | 依赖 Day 4/Day 5 的模型定义 |
| 初始化默认租户/管理员账号 | Day 6 的 `init_db.py` 任务 |
| 实现 Repository / CRUD 逻辑 | 依赖模型完成后再做 |
| 把所有接口都接数据库 | 目前还没有业务接口 |
| 实现同步数据库 session 给业务用 | 项目主链路使用异步 FastAPI，Day 3 以异步 session 为主 |

---

## 4. 逐文件实现规格

### 4.1 `backend/app/db/base.py`

**职责**：
- 定义项目所有 ORM 模型共享的基类 `Base`
- 提供公共字段 Mixin，减少后续模型重复代码
- 让 Alembic 能通过 `Base.metadata` 识别所有模型元数据

**Day 3 必须包含的内容**：

| 组成 | 说明 |
|------|------|
| `Base` | 使用 SQLAlchemy 2.0 的 `DeclarativeBase` |
| `TimestampMixin` | 提供 `created_at` / `updated_at` 公共字段 |
| （可选）`IDMixin` | 如果你想统一 UUID 主键模式，可以先预留；但 Day 3 不是必须 |

**推荐实现方向**：

```python
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""


class TimestampMixin:
    """公共时间戳字段"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

**关键约束**：
- 使用 SQLAlchemy 2.0 风格：`Mapped[...]` + `mapped_column(...)`
- Day 3 只提供公共基类，不提前写业务模型字段
- `created_at / updated_at` 尽量使用数据库侧默认值（`func.now()`）
- 代码和注释都要清楚说明：这个文件是给 Day 4/Day 5 的模型复用的

---

### 4.2 `backend/app/db/session.py`

**职责**：
- 统一创建数据库异步连接引擎
- 提供 `AsyncSession` 工厂
- 提供 FastAPI 可直接注入的 `get_db()` 依赖
- 为 `main.py` 生命周期管理提供 `engine` 引用

**Day 3 需要支持的对象**：

| 对象 | 说明 |
|------|------|
| `engine` | `create_async_engine(settings.database_url, ...)` 创建的异步引擎 |
| `AsyncSessionLocal` | `async_sessionmaker` 生成的 session 工厂 |
| `get_db()` | `yield` 一个 `AsyncSession` 给 API 层使用 |

**推荐实现方向**：

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**关键约束**：
- 使用异步引擎：`create_async_engine`
- `expire_on_commit=False` 建议开启，避免提交后对象属性访问异常
- `pool_pre_ping=True` 建议开启，减少长连接失效问题
- `get_db()` 必须使用 `yield`，这样 FastAPI 才会把它当作生命周期依赖自动回收
- Day 3 不要求写复杂的连接池参数，先保证清晰可运行

**额外建议**：
- 可以额外提供一个 `check_db_connection()` 辅助函数，供 `main.py` 的 startup 验证使用
- 但不要在 `session.py` 里写业务逻辑或 init data 逻辑

---

### 4.3 `backend/app/api/deps.py`

**职责变化**：
- 把 Day 1 的 `get_db()` 占位替换为真实数据库依赖导出
- 保留 `get_current_user()` 的占位，因为认证仍然是 Week 2 任务

**Day 3 修改后建议结构**：

```python
from app.db.session import get_db


async def get_current_user():
    raise NotImplementedError("Week 2 实现认证依赖 get_current_user")
```

**关键约束**：
- 不要在 `api/deps.py` 里重复创建 engine/sessionmaker
- `get_db()` 的单一事实来源必须是 `app.db.session`
- `get_current_user()` 继续保持可运行的最小占位，不提前引入 JWT 依赖

---

### 4.4 Alembic 初始化（`backend/alembic.ini` + `backend/app/db/migrations/`）

**职责**：
- 为数据库结构变更提供版本管理机制
- 让 Day 4/Day 5 建表时能通过 `revision --autogenerate` 自动生成迁移脚本

**Day 3 目标**：
- Alembic 框架初始化成功
- `env.py` 能读取项目的 `Base.metadata`
- `alembic upgrade head` 能运行成功

**推荐初始化方式**：

```bash
cd backend
poetry run alembic init app/db/migrations
```

生成后需要重点修改的文件：

| 文件 | 必做修改 |
|------|----------|
| `alembic.ini` | 配置 `script_location`，数据库 URL 可留空或占位，由 `env.py` 动态注入 |
| `app/db/migrations/env.py` | 从 `app.core.config` 读取 `settings.database_url_sync` 或同步版连接串；导入 `Base.metadata` |
| `app/db/migrations/versions/` | Day 3 可为空，后续存放迁移文件 |

**`env.py` 的关键点**：

1. 必须能导入项目代码：
   - 需要确保运行 Alembic 时 Python path 能找到 `app`
2. 必须绑定 metadata：
   - `target_metadata = Base.metadata`
3. 必须使用**同步**数据库 URL：
   - Alembic 迁移本身通常使用同步驱动
   - 所以建议在 Day 2 的 `config.py` 中保留一个 `database_url_sync`

**推荐实现方向**：

```python
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.core.config import settings
from app.db.base import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

target_metadata = Base.metadata
```

**关键约束**：
- 不要把 Alembic URL 写死在 `alembic.ini` 里，优先从项目配置读取
- Day 3 即使没有业务表，也要保证 Alembic 能跑起来
- `env.py` 要写注释说明：为什么迁移用同步 URL，而项目运行时用异步 URL

---

### 4.5 `backend/app/main.py`

**职责变化**：
在 Day 2 基础上，新增数据库生命周期接入：

1. 应用启动时，验证数据库引擎可用（可选做轻量检查）
2. 应用关闭时，释放数据库连接池资源（`engine.dispose()`）

**推荐实现方向**：

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup 阶段：可选做轻量连接检查
    yield
    # shutdown 阶段：释放连接池
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="企业级 SaaS 智能客服 AI 平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
```

**关键约束**：
- 优先使用 `lifespan`，不要继续扩散旧式 `@app.on_event("startup")`
- Day 3 的 startup 检查要尽量轻量，不要在启动时执行复杂 SQL
- 不要破坏 Day 2 已注册的日志中间件、异常处理器、路由挂载
- 如果当前 `main.py` 已有用户手改内容，必须以当前文件为基线增量修改，不要整文件覆盖

---

### 4.6 `backend/app/core/config.py`（仅补充，不重写）

**Day 3 需要确认的配置项**：

| 配置项 | 是否必须 | 说明 |
|--------|----------|------|
| `database_url` | 必须 | 异步运行时使用，格式如 `postgresql+asyncpg://...` |
| `database_url_sync` | 建议补充 | Alembic 迁移使用，格式如 `postgresql://...` |

**关键约束**：
- 如果 Day 2 已经有 `database_url_sync`，Day 3 不重复改
- 如果没有，Day 3 可以最小补充，但不能破坏现有 `settings` 结构
- `.env.example` 中也应保持与之对应，但如果本轮只写 spec，则在实现时再补

---

## 5. 验证标准

### 5.1 数据库容器准备

```bash
podman compose up -d postgres
```

预期：
- PostgreSQL 容器启动成功
- 本地能通过 `5432` 连接数据库

---

### 5.2 导入验证

```bash
cd backend
poetry run python -c "from app.db.base import Base, TimestampMixin; from app.db.session import engine, AsyncSessionLocal, get_db; print('ok')"
```

预期：
- 可以正常输出 `ok`
- 不出现导入错误、循环依赖错误、配置读取错误

---

### 5.3 数据库连接验证

推荐方式（轻量验证）：

```bash
cd backend
poetry run python -c "import asyncio; from sqlalchemy import text; from app.db.session import engine; async def main():\n    async with engine.begin() as conn:\n        await conn.execute(text('SELECT 1'))\n    print('db ok')\nasyncio.run(main())"
```

预期：
- 输出 `db ok`
- 不报数据库连接错误

> 如果一行命令不方便，也可以临时写成一个短脚本验证，验证后删除。

---

### 5.4 Alembic 初始化验证

```bash
cd backend
poetry run alembic current
poetry run alembic upgrade head
```

预期：
- Alembic 命令可执行
- `upgrade head` 不报错
- 数据库中出现 `alembic_version` 表

---

### 5.5 应用启动验证

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

预期：
- 后端能正常启动
- `/docs`、`/redoc`、`/api/v1/health` 不受影响
- 应用关闭时没有连接池 dispose 报错

---

## 6. 与后续开发的衔接关系

Day 3 完成后，以下内容就具备开发前提了：

| 后续阶段 | 依赖 Day 3 的内容 |
|----------|------------------|
| Day 4 ORM 模型（Part 1） | `Base` + `TimestampMixin` + Alembic metadata |
| Day 5 ORM 模型（Part 2） | 同上 |
| Day 6 API 依赖注入 | `get_db()` 真正可用 |
| Week 2 认证接口 | 登录逻辑需要数据库查询用户 |
| Week 5 审计 / 工单 / Agent 持久化 | 都要基于统一 session 与模型体系 |

---

## 7. Day 3 完成标准（DoD）

完成 Day 3，至少要满足以下检查项：

- [ ] `backend/app/db/base.py` 已创建，包含 `Base`
- [ ] `backend/app/db/base.py` 已包含公共时间戳 Mixin
- [ ] `backend/app/db/session.py` 已创建，包含 `engine`
- [ ] `backend/app/db/session.py` 已包含 `AsyncSessionLocal`
- [ ] `backend/app/db/session.py` 已包含 `get_db()`
- [ ] `backend/app/api/deps.py` 已改为导出真实 `get_db()`
- [ ] `backend/alembic.ini` 已存在
- [ ] `backend/app/db/migrations/env.py` 已绑定 `Base.metadata`
- [ ] `poetry run alembic upgrade head` 能执行成功
- [ ] 数据库中能看到 `alembic_version` 表
- [ ] `poetry run uvicorn app.main:app --reload` 仍能正常启动
- [ ] `/api/v1/health` 仍然正常返回 200
- [ ] 代码写有清晰中文注释，便于你后续复盘

---

## 8. 常见坑与排错建议

### 8.1 `ModuleNotFoundError: No module named 'app'`

**原因**：
Alembic 执行时，Python path 没有正确找到 `backend/app`

**排查方向**：
- 确认命令是在 `backend/` 目录执行的
- 检查 `env.py` 中是否用了错误的相对导入
- 必要时在 `env.py` 中补充项目根路径注入逻辑

---

### 8.2 `sqlalchemy.exc.NoSuchModuleError`

**原因**：
数据库 URL 驱动写错，比如异步 URL / 同步 URL 混用了

**排查方向**：
- 运行时 URL：`postgresql+asyncpg://...`
- Alembic URL：`postgresql://...`
- 不要把 `asyncpg` URL 直接给 Alembic 用

---

### 8.3 `Connection refused`

**原因**：
PostgreSQL 容器没启动，或账号密码/库名不一致

**排查方向**：
- 先执行 `podman compose up -d postgres`
- 检查 `compose.yml` 里的数据库用户名、密码、数据库名
- 检查 `settings.database_url` / `database_url_sync` 是否对应一致

---

### 8.4 `Target database is not up to date` / `Can't locate revision`

**原因**：
Alembic 版本状态异常，或初始化步骤不完整

**排查方向**：
- 确认 `app/db/migrations/versions/` 目录存在
- 确认 `alembic.ini` 的 `script_location` 正确
- Day 3 初次初始化时，优先先跑通空迁移框架，不要急着 autogenerate 业务表

---

### 8.5 `get_db()` 没有被正确释放

**原因**：
依赖函数没有用 `yield`，或者 `finally` 没有关闭 session

**正确模式**：

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## 9. 实施顺序建议

为了减少返工，Day 3 推荐按这个顺序实现：

1. 先写 `db/base.py`
2. 再写 `db/session.py`
3. 再修改 `api/deps.py`
4. 再初始化 Alembic 并改 `env.py`
5. 最后再把 `main.py` 接入 `lifespan`
6. 按验证清单逐项验证

这样做的好处是：
- 先把可导入的基础设施搭好
- 再做对外依赖接入
- 最后才碰入口文件，减少启动失败时的排查难度
