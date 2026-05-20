"""
SupportForge 后端应用入口

这个文件是整个后端服务的启动点，职责是：
1. 创建 FastAPI 应用实例（配置标题、描述、版本号）
2. 挂载路由（将 api_router 注册到 /api/v1 前缀下）
3. 为后续中间件和生命周期事件预留接入位置

设计原则：
- main.py 只做"注册和挂载"，不写任何业务逻辑
- 所有接口路由都在 api/v1/ 目录下定义，通过 router.py 聚合后统一挂载
- 这样做的好处是：每个模块独立维护，main.py 保持简洁稳定
"""

from fastapi import FastAPI
from .api.v1.router import api_router

# 创建 FastAPI 应用实例
# title/description/version 会显示在 Swagger 文档页面（/docs）
# docs_url="/docs" — 开发阶段可访问 Swagger UI，生产阶段可通过 config 关闭
# redoc_url="/redoc" — 提供 ReDoc 格式的文档，风格更简洁
app = FastAPI(
    title="SupportForge",
    description="企业级 SaaS 智能客服 AI 平台",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 挂载 v1 版本路由
# prefix="/api/v1" — 所有接口的统一前缀，与接口文档约定一致
# 例如 /api/v1/health、/api/v1/auth/login、/api/v1/tenants 等
app.include_router(api_router, prefix="/api/v1")

# ────────────────────────────────────────────────────
# 以下为后续开发预留位置，Day 1 不实现，只留注释
# ────────────────────────────────────────────────────

# TODO: Day 2 — 注册全局异常处理器（BusinessException、UnauthorizedException 等）
# TODO: Day 2 — 注册日志中间件（请求/响应日志、request_id 注入）
# TODO: Day 3 — 注册数据库生命周期事件（startup 时连接数据库，shutdown 时关闭连接）