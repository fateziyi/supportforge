"""
v1 版本路由聚合器

这个文件是所有 v1 接口的路由入口，职责是：
1. 聚合所有 v1 版本的子路由模块
2. 统一管理每个模块的前缀（prefix）和标签（tags）
3. 被 main.py 通过 app.include_router() 挂载到 /api/v1 下

设计说明：
- 每个业务模块（auth、tenants、users 等）都有自己的 router
- 在这个文件里通过 include_router() 把它们统一聚合
- 最终在 main.py 只需要一行 app.include_router(api_router, prefix="/api/v1")

路由层级关系：
  main.py → include_router(api_router, prefix="/api/v1")
    api_router → include_router(health_router, tags=["health"])
    api_router → include_router(auth_router)  ← Day 6 已挂载
    api_router → include_router(
        tenants_router, prefix="/tenants", tags=["tenants"]
    )  ← Week 2
    ...

最终用户访问的 URL：
  /api/v1/health         → 健康检查
  /api/v1/auth/login     → 登录接口（Day 6 mock，Week 2 真实 JWT）
  /api/v1/tenants        → 租户列表（Week 2）
"""

from fastapi import APIRouter

# 导入各模块的路由
from .auth import router as auth_router
from .health import router as health_router

# 创建聚合路由实例
# 注意：这里不加 prefix，因为 prefix 在 main.py 中统一设置
# 每个子模块自己的 prefix 在 include_router 时单独指定
api_router = APIRouter()

# ─── 挂载已实现的模块 ───

# 健康检查模块 — 不需要 prefix，直接暴露为 /api/v1/health
api_router.include_router(health_router, tags=["health"])

# 认证模块 — Day 6 已实现 mock 登录骨架
# auth_router 自带 prefix="/auth"，所以最终路径是 /api/v1/auth/login
api_router.include_router(auth_router)

# ─── 后续模块挂载位置（Week 2 开始逐步添加）───

# api_router.include_router(tenants_router, prefix="/tenants", tags=["tenants"])
# api_router.include_router(users_router, prefix="/users", tags=["users"])
# api_router.include_router(
#     knowledge_bases_router, prefix="/knowledge-bases", tags=["knowledge-bases"]
# )
# api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
# api_router.include_router(
#     conversations_router, prefix="/conversations", tags=["conversations"]
# )
# api_router.include_router(tickets_router, prefix="/tickets", tags=["tickets"])
# api_router.include_router(
#     audit_logs_router, prefix="/audit-logs", tags=["audit-logs"]
# )
