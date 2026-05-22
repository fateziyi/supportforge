# Day 2 Spec：配置管理 + 日志初始化 + 统一异常处理 + 请求上下文

> 目标：在 Day 1 已能启动 FastAPI 的基础上，为后端补齐**全局配置能力、日志能力、统一错误处理能力、请求级上下文能力**，让项目具备真正可扩展的工程化基座。

---

## 1. Day 2 要解决什么问题

Day 1 只是把后端服务跑起来了，但还存在 4 个核心缺口：

1. **配置散落**：数据库、Redis、Qdrant、JWT、OpenAI 等配置还没有统一入口
2. **日志不可控**：没有统一日志格式，后续出问题很难排查
3. **异常返回不统一**：接口失败时没有统一结构，前端不好接，排错也混乱
4. **请求上下文缺失**：后续做多租户与审计时，需要在请求生命周期内拿到 `request_id / user_id / tenant_id`

Day 2 就是解决这 4 个问题。

---

## 2. Day 2 目标产出

完成后新增 / 修改的核心文件如下：

```text
backend/app/
├── main.py                          # 需要补充异常处理器注册 + 日志中间件注册
├── core/
│   ├── __init__.py
│   ├── config.py                    # 配置管理
│   ├── logging.py                   # 日志初始化与日志中间件
│   ├── exceptions.py                # 自定义异常 + 全局异常处理器
│   └── context.py                   # 请求级上下文（request_id / tenant_id / user_id）
└── api/
    └── v1/
        └── health.py                # 可选：继续保持简单返回，不强制改统一结构
```

---

## 3. Day 2 实现边界

### Day 2 要做

| 模块 | 内容 |
|------|------|
| `core/config.py` | 统一读取环境变量，提供 settings 单例 |
| `core/logging.py` | 初始化日志格式，编写 `RequestLogMiddleware` |
| `core/exceptions.py` | 定义业务异常类，注册全局异常处理器 |
| `core/context.py` | 使用 `ContextVar` 保存 `request_id / tenant_id / user_id` |
| `main.py` | 接入：加载 settings、注册异常处理器、注册日志中间件 |
| 验证 | 启动成功、错误接口返回统一结构、日志中能看到 request_id |

### Day 2 不做

| 不做 | 原因 |
|------|------|
| 实现数据库连接 | Day 3 任务 |
| 实现 JWT 登录认证 | Week 2 任务 |
| 实现真实 `tenant_id / user_id` 注入 | Week 2 任务 |
| 实现业务 API 接口 | 认证完成后再做 |
| 改造所有接口返回统一结构 | Day 2 只先打通错误返回与基础能力 |
| 写测试用例 | Week 6 任务 |

---

## 4. 逐文件实现规格

### 4.1 `backend/app/core/config.py`

**职责**：
- 统一管理项目配置项
- 从环境变量读取配置，避免把密码、密钥硬编码在代码中
- 提供全局 `settings` 对象，供其他模块直接导入使用

**Day 2 必须包含的配置项**：

| 配置项 | 来源 | 说明 |
|--------|------|------|
| `app_name` | 固定默认值 | `SupportForge` |
| `app_env` | `.env` / 默认值 | `development` / `test` / `production` |
| `app_port` | `.env` / 默认值 | 默认 `8000` |
| `log_level` | `.env` / 默认值 | 默认 `INFO` |
| `jwt_secret_key` | `.env` / 默认值 | Day 2 先只读，不使用 |
| `jwt_algorithm` | `.env` / 默认值 | Day 2 先只读，不使用 |
| `access_token_expire_minutes` | `.env` / 默认值 | Day 2 先只读，不使用 |
| `refresh_token_expire_days` | `.env` / 默认值 | Day 2 先只读，不使用 |
| `database_url` | `.env` / 默认值 | Day 3 要用 |
| `redis_url` | `.env` / 默认值 | Week 5 要用 |
| `qdrant_url` | `.env` / 默认值 | Week 3 要用 |
| `openai_api_key` | `.env` / 默认值 | Week 3/4 要用 |
| `openai_model_name` | `.env` / 默认值 | Week 3/4 要用 |

**实现要求**：
- 使用 `pydantic-settings`（如果当前依赖没有，再临时用 `os.getenv` + dataclass/simple class）
- 提供 `settings = Settings()` 单例
- 所有字段配中文注释，便于你后续阅读理解

**建议代码结构**：

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "SupportForge"
    app_env: str = "development"
    app_port: int = 8000
    log_level: str = "INFO"
    ...

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
```

**关键约束**：
- 不要把真实敏感值写死在代码里
- 如果 `.env` 不存在，也应该能依赖默认值启动
- 配置项命名要和 `backend/.env.example` 基本一致

---

### 4.2 `backend/app/core/context.py`

**职责**：
- 保存请求生命周期内的上下文信息
- 让后续日志、审计、多租户过滤都可以读取当前请求的上下文

**Day 2 需要支持的上下文字段**：

| 字段 | 说明 | 来源 |
|------|------|------|
| `request_id` | 每个请求唯一 ID | Day 2 的日志中间件生成 |
| `user_id` | 当前用户 ID | Week 2 从 JWT 注入 |
| `tenant_id` | 当前租户 ID | Week 2 从 JWT 注入 |

**实现要求**：
- 使用 `ContextVar`
- 提供 `set_request_id()` / `get_request_id()` / `clear_context()` 等函数
- Day 2 先只要求 `request_id` 真正可用，`user_id` 和 `tenant_id` 可以先留空

**建议代码结构**：

```python
from contextvars import ContextVar
from typing import Optional

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
```

**关键约束**：
- 提供统一 getter/setter，不直接在业务代码里操作底层 `ContextVar`
- `clear_context()` 必须存在，避免请求之间上下文串数据

---

### 4.3 `backend/app/core/logging.py`

**职责**：
- 初始化项目统一日志格式
- 提供请求日志中间件
- 将 `request_id` 注入日志上下文，便于排查问题

**Day 2 要达到的效果**：
- 每次请求进入时，自动生成一个 `request_id`
- 请求结束时，打印一条结构化日志，至少包含：
  - `request_id`
  - `method`
  - `path`
  - `status_code`
  - `duration_ms`

**实现要求**：
- 提供 `setup_logging()` 函数
- 提供 `RequestLogMiddleware` 中间件类
- 中间件里：
  1. 生成 `request_id`（可以用 `uuid.uuid4()`）
  2. 写入 `ContextVar`
  3. 调用下游请求处理器
  4. 记录耗时与状态码
  5. 请求结束后清理上下文

**建议日志格式**：

```text
[2026-05-20 14:30:00] INFO request_id=xxx method=GET path=/api/v1/health status=200 duration_ms=3
```

**关键约束**：
- Day 2 使用 Python 标准库 `logging` 即可，不引入复杂日志框架
- 中间件必须保证异常情况下也能清理 context
- 中间件代码要写详细中文注释，解释 `call_next` 和 `duration_ms` 的含义

---

### 4.4 `backend/app/core/exceptions.py`

**职责**：
- 定义项目统一异常类型
- 提供全局异常处理器，把错误统一转成标准 JSON 结构

**Day 2 要支持的异常类型**：

| 异常类 | 场景 | HTTP 状态码 |
|--------|------|-------------|
| `BusinessException` | 通用业务异常 | 400 |
| `UnauthorizedException` | 未登录/Token 无效 | 401 |
| `ForbiddenException` | 已登录但无权限 | 403 |
| `NotFoundException` | 资源不存在 | 404 |

**统一错误返回结构**：

```json
{
  "code": 40001,
  "message": "资源不存在",
  "data": null
}
```

**实现要求**：
- 定义异常基类，包含：
  - `code`
  - `message`
  - `status_code`
- 提供 3 类 handler：
  1. 自定义业务异常 handler
  2. `HTTPException` handler
  3. 未知异常 handler
- 提供 `register_exception_handlers(app)` 函数供 `main.py` 调用

**关键约束**：
- 未知异常不要把堆栈直接暴露给前端
- 未知异常对前端统一返回：`500 + "Internal Server Error"`
- Day 2 先只做错误返回统一，不要求成功返回也统一包装

---

### 4.5 `backend/app/main.py`

**职责变化**：
在 Day 1 基础上，新增 3 个接入动作：

1. 导入并初始化 `settings`
2. 注册日志系统与请求日志中间件
3. 注册全局异常处理器

**Day 2 修改后建议结构**：

```python
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging, RequestLogMiddleware
from app.core.exceptions import register_exception_handlers

setup_logging()

app = FastAPI(
    title=settings.app_name,
    description="企业级 SaaS 智能客服 AI 平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(RequestLogMiddleware)
register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")
```

**关键约束**：
- 不能破坏 Day 1 已通过的 `/docs`、`/redoc`、`/api/v1/health`
- 引入 settings 后，`title` 改成从配置读取
- 如果用户已经手动修改了 `main.py`，应以当前文件为基线增量修改，不覆盖用户改动

---

## 5. 验证标准

### 5.1 启动验证

```bash
cd backend
poetry run uvicorn app.main:app --reload
```

预期：
- 后端能正常启动
- `/docs` 和 `/redoc` 仍然可访问
- `/api/v1/health` 仍然返回 200

---

### 5.2 配置验证

```bash
cd backend
poetry run python -c "from app.core.config import settings; print(settings.app_name, settings.app_env, settings.log_level)"
```

预期：
- 能输出 `SupportForge development INFO`（或你本地 `.env` 中对应值）

---

### 5.3 异常处理验证

需要额外创建一个临时测试接口（或临时在 `health.py` 中加测试路由，验证后删除）。

推荐临时测试方式：

```python
@router.get("/health-error")
async def health_error():
    raise BusinessException(message="手动测试业务异常", code=40001)
```

然后执行：

```bash
curl http://localhost:8000/api/v1/health-error
```

预期返回：

```json
{
  "code": 40001,
  "message": "手动测试业务异常",
  "data": null
}
```

验证完成后可以删除该临时接口。

---

### 5.4 日志验证

访问一次健康检查接口：

```bash
curl http://localhost:8000/api/v1/health
```

预期终端日志至少包含：
- `request_id=`
- `method=GET`
- `path=/api/v1/health`
- `status=200`
- `duration_ms=`

---

### 5.5 Lint 验证

```bash
cd backend
poetry run ruff check app/
poetry run black --check app/
```

预期：全部通过。

---

## 6. Day 2 完成定义（Definition of Done）

满足以下全部条件，才算 Day 2 完成：

- [ ] 已创建 `core/config.py`
- [ ] 已创建 `core/logging.py`
- [ ] 已创建 `core/exceptions.py`
- [ ] 已创建 `core/context.py`
- [ ] `main.py` 已接入 settings / logging / exception handlers
- [ ] 项目仍能正常启动
- [ ] `/api/v1/health` 仍可访问
- [ ] 至少能验证一类统一错误返回
- [ ] 日志中能看到 `request_id`
- [ ] `ruff` / `black` 通过

---

## 7. 常见失败与排查方法

### 7.1 导入 `BaseSettings` 失败

如果报错类似：

```text
ModuleNotFoundError: No module named 'pydantic_settings'
```

说明当前依赖里没有 `pydantic-settings`。

**处理方式**：
- 方案 A：把 `pydantic-settings` 加到 `pyproject.toml`（推荐）
- 方案 B：Day 2 先用 `os.getenv()` + 普通类实现，Day 3/Week 2 再升级

建议优先方案 A，因为后续配置会越来越多。

---

### 7.2 中间件报错导致所有请求失败

优先检查：
- `dispatch()` 方法签名是否正确
- 是否正确调用了 `response = await call_next(request)`
- 是否在 `finally` 中清理上下文

---

### 7.3 异常处理器没有生效

优先检查：
- `register_exception_handlers(app)` 是否真的在 `main.py` 调用了
- 抛出的异常是否是你自定义的异常类
- 是否被 FastAPI 默认异常处理器抢先处理了

---

## 8. 与后续任务的衔接

| 后续阶段 | 依赖 Day 2 的什么能力 |
|----------|----------------------|
| Day 3 数据库连接 | `settings.database_url` |
| Week 2 JWT 认证 | `settings.jwt_secret_key` + `context.py` |
| Week 2 多租户隔离 | `context.py` 中的 `tenant_id` |
| Week 5 审计日志 | `request_id / user_id / tenant_id` 上下文 |
| Week 6 问题排查与演示 | 请求日志 + 统一错误返回 |

---

## 9. 实现完成记录

> 本章节记录 Day 2 spec 实际完成情况，包含产出文件、验证结果、与 spec 的偏差说明。

### 完成时间

2026-05-20

### 实际产出文件

| 文件 | 说明 |
|------|------|
| `backend/app/core/config.py` | Settings 类（pydantic-settings），含全部配置项 + `database_url_sync` |
| `backend/app/core/context.py` | ContextVar 存储 request_id / user_id / tenant_id |
| `backend/app/core/exceptions.py` | 5 类异常处理器（Starlette / FastAPI / App / ValidationError / Generic） |
| `backend/app/core/logging.py` | setup_logging() + RequestLogMiddleware |
| `backend/app/main.py` | 接入 settings、日志中间件、异常处理器 |

### 验证结果

- ✅ `poetry run python -c "from app.core.config import settings; print(settings.app_name)"` → `SupportForge`
- ✅ `poetry run uvicorn app.main:app` 正常启动
- ✅ `/api/v1/health` 返回 200
- ✅ 404 请求返回统一格式：`{"code":40400,"message":"Not Found","data":null}`
- ✅ 日志中能看到 `request_id`、`method`、`path`、`status`、`duration_ms`
- ✅ `ruff check app/` 通过
- ✅ `black --check app/` 通过

### 与 Spec 的偏差

1. **异常处理器扩展**：Spec 原始计划 3 类 handler（业务异常 / HTTPException / 未知异常），实作时扩展为 5 类：
   - 增加 `StarletteHTTPException` handler（解决 404 返回 `{"detail":"Not Found"}` 的问题）
   - 增加 `RequestValidationError` handler（FastAPI 参数校验错误也统一格式）
   - 所有 `add_exception_handler` 加了 `# type: ignore[arg-type]`（已知 FastAPI 类型限制）

2. **`_error_response` 修复**：原始实现中 `status_code=code if code < 600 else 400` 有 bug（业务码 40400 > 600 导致返回 400），修复为 `http_status = status_code if status_code else max(400, min(599, code // 100))`

3. **`database_url_sync` 提前补充**：Day 2 spec 没提到这个配置项，但实作时提前加入了 `config.py`，为 Day 3 Alembic 做准备

4. **新增依赖**：`pydantic-settings ^2.14.1`（Spec 推荐方案 A，实作采纳）

Day 2 做完之后，这个项目才真正进入“可扩展的企业级后端骨架”状态。