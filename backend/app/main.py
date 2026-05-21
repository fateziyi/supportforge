"""
SupportForge 后端应用入口

这个文件是整个后端服务的启动点，职责是：
1. 创建 FastAPI 应用实例（配置标题、描述、版本号）
2. 挂载路由（将 api_router 注册到 /api/v1 前缀下）
3. 注册日志中间件（记录每个请求的 request_id、耗时、状态码）
4. 注册全局异常处理器（统一错误返回格式）

设计原则：
- main.py 只做"注册和挂载"，不写任何业务逻辑
- 所有接口路由都在 api/v1/ 目录下定义，通过 router.py 聚合后统一挂载
- 这样做的好处是：每个模块独立维护，main.py 保持简洁稳定

接入顺序说明（Day 2 新增）：
1. setup_logging() → 初始化日志系统，必须在 app 创建前调用
2. app.add_middleware(RequestLogMiddleware) → 添加请求日志中间件
3. register_exception_handlers(app) → 注册全局异常处理器
"""

from fastapi import FastAPI

# ── 导入路由 ──
from .api.v1.router import api_router

# ── 导入 Day 2 新增的核心模块 ──
from .core.config import settings              # 配置管理（Day 2）
from .core.logging import setup_logging, RequestLogMiddleware  # 日志（Day 2）
from .core.exceptions import register_exception_handlers      # 异常处理（Day 2）

# ── 初始化日志系统 ──
# 必须在创建 FastAPI 实例之前调用，否则早期日志无法正常输出
# log_level 从 settings 中读取，可通过 .env 文件调整
setup_logging(log_level=settings.log_level)

# ── 创建 FastAPI 应用实例 ──
# title 从 settings 中读取，不再硬编码
# description/version/docs_url/redoc_url 保持不变
app = FastAPI(
    title=settings.app_name,
    description="企业级 SaaS 智能客服 AI 平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── 注册中间件 ──
# RequestLogMiddleware: 记录每个请求的 request_id、method、path、status、duration_ms
# add_middleware 的参数是中间件类本身（不是实例），FastAPI 会自动创建实例
app.add_middleware(RequestLogMiddleware)

# ── 注册全局异常处理器 ──
# register_exception_handlers 会把 AppException、HTTPException、Exception
# 三类异常处理器全部注册到 app 上
# 注册后，所有错误返回都会遵循统一格式：{"code": xxx, "message": "xxx", "data": null}
register_exception_handlers(app)

# ── 挂载路由 ──
# prefix="/api/v1" — 所有接口的统一前缀，与接口文档约定一致
# 例如 /api/v1/health、/api/v1/auth/login、/api/v1/tenants 等
app.include_router(api_router, prefix="/api/v1")

# ────────────────────────────────────────────────────
# 以下为后续开发预留位置
# ────────────────────────────────────────────────────

# TODO: Day 3 — 注册数据库生命周期事件（startup 时连接数据库，shutdown 时关闭连接）