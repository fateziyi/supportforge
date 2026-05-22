"""
SupportForge 后端应用入口

这个文件是整个后端服务的启动点，职责是：
1. 创建 FastAPI 应用实例（配置标题、描述、版本号）
2. 挂载路由（将 api_router 注册到 /api/v1 前缀下）
3. 注册日志中间件（记录每个请求的 request_id、耗时、状态码）
4. 注册全局异常处理器（统一错误返回格式）
5. 注册数据库生命周期（启动时准备连接，关闭时释放连接池）

设计原则：
- main.py 只做"注册和挂载"，不写任何业务逻辑
- 所有接口路由都在 api/v1/ 目录下定义，通过 router.py 聚合后统一挂载
- 这样做的好处是：每个模块独立维护，main.py 保持简洁稳定

接入顺序说明：
1. setup_logging() → 初始化日志系统，必须在 app 创建前调用（Day 2）
2. app.add_middleware(RequestLogMiddleware) → 添加请求日志中间件（Day 2）
3. register_exception_handlers(app) → 注册全局异常处理器（Day 2）
4. lifespan → 数据库连接池的启动与释放（Day 3）
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

# ── 导入路由 ──
from .api.v1.router import api_router

# ── 导入 Day 2 新增的核心模块 ──
from .core.config import settings  # 配置管理（Day 2）
from .core.exceptions import register_exception_handlers  # 异常处理（Day 2）
from .core.logging import RequestLogMiddleware, setup_logging  # 日志（Day 2）

# ── 导入 Day 3 新增的数据库模块 ──
from .db.session import engine  # 数据库引擎（Day 3）


# ── 定义应用生命周期管理 ──
# lifespan 是 FastAPI 2.0+ 推荐的启动/关闭管理方式
# 使用 asynccontextmanager + yield 模式：
# - yield 之前的内容在应用启动时执行（startup）
# - yield 之后的内容在应用关闭时执行（shutdown）
#
# 为什么用 lifespan 而不是 @app.on_event("startup")？
# - on_event 是旧式 API，FastAPI 官方文档已标记为 deprecated
# - lifespan 支持 async，可以和数据库引擎等异步资源配合
# - lifespan 更容易测试和复用
#
# Day 3 的 lifespan 只做两件事：
# 1. startup: 不做重操作（不发 SELECT 1，避免启动变慢）
# 2. shutdown: 释放数据库引擎的连接池资源
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    startup 阶段（yield 之前）：
    - 目前不做重操作，只让日志记录"应用已启动"
    - 不在这里验证数据库连接，避免启动变慢
    - 数据库连接验证在首次请求时自动发生（pool_pre_ping=True）

    shutdown 阶段（yield 之后）：
    - 释放数据库引擎的连接池
    - engine.dispose() 关闭所有连接，归还给操作系统
    - 防止进程退出后连接池中的连接成为"僵尸连接"
    """
    # ── startup 阶段 ──
    # 获取日志实例，记录启动信息
    import logging
    logger = logging.getLogger("app")
    logger.info(
        f"SupportForge 启动 | env={settings.app_env} |"
        f" port={settings.app_port}"
    )

    # yield 把控制权交给 FastAPI，开始处理请求
    yield

    # ── shutdown 阶段 ──
    # 释放数据库引擎的连接池资源
    # engine.dispose() 会关闭所有空闲连接，正在使用的连接会在请求完成后自动释放
    # 这是应用关闭时必须做的事情，否则连接池中的连接不会被正确关闭
    logger.info("SupportForge 关闭 | 释放数据库连接池")
    await engine.dispose()


# ── 初始化日志系统 ──
# 必须在创建 FastAPI 实例之前调用，否则早期日志无法正常输出
# log_level 从 settings 中读取，可通过 .env 文件调整
setup_logging(log_level=settings.log_level)

# ── 创建 FastAPI 应用实例 ──
# title 从 settings 中读取，不再硬编码
# lifespan 参数传入上面定义的生命周期管理函数
# FastAPI 会自动在启动时执行 lifespan 的 yield 前部分
# 在关闭时执行 yield 后部分
app = FastAPI(
    title=settings.app_name,
    description="企业级 SaaS 智能客服 AI 平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
