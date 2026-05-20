# Day 1 Spec：FastAPI 入口 + 项目目录结构

> 目标：让后端能跑起来，访问 `http://localhost:8000/docs` 看到 Swagger 页面，并建立后续 Week 1 开发所需的最小后端骨架。

---

## 1. 目标产出

完成后 `backend/app/` 目录结构如下：

```text
backend/app/
├── __init__.py
├── main.py                    # FastAPI 应用入口
├── core/
│   └── __init__.py
├── db/
│   └── __init__.py
├── models/
│   └── __init__.py
├── schemas/
│   └── __init__.py
├── api/
│   ├── __init__.py
│   ├── deps.py                # 依赖注入骨架
│   └── v1/
│       ├── __init__.py
│       ├── router.py          # v1 路由聚合
│       └── health.py          # 健康检查接口
├── services/
│   └── __init__.py
├── repositories/
│   └── __init__.py
├── rag/
│   └── __init__.py
├── tasks/
│   └── __init__.py
├── integrations/
│   └── __init__.py
├── utils/
│   └── __init__.py
└── agent/
    ├── __init__.py
    └── prompts/
        ├── agent.md           # 已有
        ├── classify.md        # 已有
        ├── respond.md         # 已有
        ├── escalate.md        # 已有
        └── system.md          # 已有
```

### Day 1 最小完成目标

Day 1 不追求业务功能，只追求以下 3 件事：

1. **FastAPI 能启动**
2. **Swagger 文档可访问**
3. **`/api/v1/health` 健康检查接口可访问**

---

## 2. 实现边界

### Day 1 要做

| 模块 | 内容 |
|------|------|
| 目录结构 | 创建后端基础目录与 `__init__.py` |
| 入口 | 创建 `app/main.py` |
| 路由 | 创建 `api/v1/router.py` 和 `api/v1/health.py` |
| 依赖骨架 | 创建 `api/deps.py`，但只保留骨架，不落具体实现 |
| 运行验证 | 本地启动成功、Swagger 可访问、健康检查可访问 |

### Day 1 不做

| 不做 | 原因 |
|------|------|
| 实现配置管理 `config.py` | Day 2 任务 |
| 实现日志初始化 | Day 2 任务 |
| 实现统一异常处理与统一响应结构 | Day 2 任务 |
| 实现数据库连接、Session 依赖 | Day 3 任务 |
| 实现 JWT 登录认证 | Week 2 任务 |
| 实现 ORM 模型 | Day 4-5 任务 |
| 实现任何业务接口（auth / tenants / users 等） | Week 2 之后任务 |
| 创建测试目录和测试用例 | Week 6 任务 |

---

## 3. 逐文件实现规格

### 3.1 `backend/app/main.py`

**职责**：
- 创建 FastAPI 应用实例
- 挂载基础路由
- 为后续中间件、生命周期事件预留接入位置

**实现要求**：

```python
from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(
    title="SupportForge",
    description="企业级 SaaS 智能客服 AI 平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix="/api/v1")
```

**关键约束**：
- `docs_url` 使用 `/docs`
- `redoc_url` 使用 `/redoc`
- API 总前缀必须是 `/api/v1`，与接口文档保持一致
- 不在 `main.py` 中写任何业务逻辑
- Day 1 不强制加入中间件、startup/shutdown 事件，但可以留注释占位

**可选预留注释**：

```python
# TODO: Day 2 注册全局异常处理器、日志中间件
# TODO: Day 3 注册数据库相关生命周期事件
```

---

### 3.2 `backend/app/api/v1/router.py`

**职责**：
- 聚合所有 v1 子路由
- 作为 `app.include_router()` 的唯一入口

**实现要求**：

```python
from fastapi import APIRouter
from app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
```

**关键约束**：
- `health` 路由直接暴露为 `/api/v1/health`
- 后续模块统一在这个文件追加挂载
- 每个业务模块后续都需要独立 `prefix` 和 `tags`

**后续追加示例**：

```python
# api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
# api_router.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
```

---

### 3.3 `backend/app/api/v1/health.py`

**职责**：
- 提供基础探活接口
- 用于本地开发、Docker healthcheck、CI 启动验证

**实现要求**：

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "supportforge-backend",
    }
```

**关键约束**：
- 必须是**无认证接口**
- Day 1 允许直接返回简单字典，不强制套统一响应结构
- Day 2 完成统一响应封装后，再决定是否把 `/health` 也纳入统一结构

**说明**：
当前接口通用约定要求统一响应结构为：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

但 Day 1 的 `/health` 属于基础探活接口，允许作为临时例外，以便更简单地用于容器探活与初始验证。

---

### 3.4 `backend/app/api/deps.py`

**职责**：
- 定义全局共享依赖的占位骨架
- 为 Day 3 数据库依赖、Week 2 认证依赖预留位置

**实现要求**：

```python
async def get_db():
    raise NotImplementedError("Day 3 实现数据库依赖 get_db")

async def get_current_user():
    raise NotImplementedError("Week 2 实现认证依赖 get_current_user")
```

**关键约束**：
- Day 1 **不要**写 `Annotated[???]` 这类无法运行的占位代码
- Day 1 **不要**引入 `AsyncSession`、`Depends`、`oauth2_scheme`、`CurrentUser` 等尚未定义的类型或依赖
- 文件可以只有最小骨架，确保导入时不会因语法错误失败

**为什么这样设计**：
- Day 1 的目标是能启动，不是把依赖系统一次性写完
- `get_db()` 依赖 Day 3 的 `db/session.py`
- `get_current_user()` 依赖 Week 2 的 JWT 认证模块

---

### 3.5 所有 `__init__.py`

**职责**：
- 让 Python 将目录识别为包
- 为后续模块扩展预留位置

**要求**：
- 除 `models/__init__.py` 可保留注释外，其余文件可以为空
- `models/__init__.py` 建议预留 Alembic 识别说明注释

**示例**：

```python
# Week 1 Day 4-5: 导入所有 ORM 模型，让 Alembic 能识别
# from app.models.tenant import Tenant
# from app.models.user import User
```

---

## 4. 验证标准

### 4.1 本地启动验证

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

访问以下 URL，预期结果如下：

| URL | 预期结果 |
|-----|---------|
| `http://localhost:8000/docs` | Swagger UI 页面可打开 |
| `http://localhost:8000/redoc` | ReDoc 页面可打开 |
| `http://localhost:8000/api/v1/health` | 返回 `{"status": "ok", "service": "supportforge-backend"}` |

---

### 4.2 Lint 检查

```bash
cd backend
poetry run ruff check app/
poetry run black --check app/
```

预期：
- Ruff 检查通过
- Black 格式检查通过

---

### 4.3 目录完整性检查

```bash
find backend/app -name "*.py" | sort
```

预期：
- 输出中包含本 spec 中列出的所有 `.py` 文件
- 无明显遗漏目录

---

## 5. Day 1 完成定义（Definition of Done）

满足以下全部条件，才算 Day 1 完成：

- [ ] `backend/app/` 基础目录全部创建完成
- [ ] 所有必要的 `__init__.py` 文件已创建
- [ ] `backend/app/main.py` 可被 `uvicorn` 正常启动
- [ ] `http://localhost:8000/docs` 可访问
- [ ] `http://localhost:8000/api/v1/health` 可访问
- [ ] `ruff check app/` 通过
- [ ] `black --check app/` 通过
- [ ] 没有提前实现 Day 2/Day 3 的内容

---

## 6. 常见失败与排查方法

### 6.1 `ModuleNotFoundError: No module named 'app'`

**原因**：
- 没有在 `backend/` 目录下启动
- `app/__init__.py` 缺失

**排查**：

```bash
cd backend
poetry run python -c "import app"
```

如果这条命令失败，优先检查 `backend/app/__init__.py` 是否存在。

---

### 6.2 `poetry install` 失败

**排查**：

```bash
cd backend
poetry env info
poetry install -vvv
```

常见原因：
- 本地 Python 版本不在要求范围内
- Poetry 虚拟环境损坏

---

### 6.3 `uvicorn` 启动失败

**排查**：

```bash
cd backend
poetry run python -c "from app.main import app; print(app.title)"
```

如果这里失败，优先检查：
- `main.py` 的导入路径是否正确
- `router.py` / `health.py` 是否存在语法错误

---

### 6.4 8000 端口被占用

**排查**：

```bash
lsof -i :8000
```

如果端口被占用，可以临时改用：

```bash
poetry run uvicorn app.main:app --reload --port 8001
```

---

## 7. 依赖前提

| 前提 | 状态 |
|------|------|
| `backend/pyproject.toml` + `backend/poetry.lock` | ✅ 已存在 |
| Poetry 可用 | ⚠️ 需本地确认 |
| Python 版本满足 `>=3.10,<3.13` | ⚠️ 需确认 |
| 推荐 Python 版本 | 3.12 |

### Day 1 开始前先确认

```bash
cd backend
poetry install
poetry run python --version
```

确认：
- 依赖安装成功
- Python 版本在 `3.10 ~ 3.12` 范围内

---

## 8. 与后续任务的衔接

| Day / Week | 后续内容 | 当前预留点 |
|------------|----------|------------|
| Day 2 | config / logging / exceptions / context | `main.py` 预留注释位置 |
| Day 3 | db/base.py / db/session.py / Alembic | `api/deps.py` 里的 `get_db()` 占位 |
| Week 2 | JWT / RBAC / 当前用户上下文 | `api/deps.py` 里的 `get_current_user()` 占位 |

这样设计的目的，是保证 Day 1 实现最小闭环，同时不和后续开发顺序冲突。