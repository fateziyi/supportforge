"""
健康检查接口

这个接口的用途：
1. 本地开发时，验证后端服务是否正常启动
2. Docker 容器健康检查（docker-compose.yml 里 healthcheck 会调用这个接口）
3. CI 流水线验证后端可用性

设计说明：
- 这是一个无认证接口，任何人都可以访问
- Day 1 阶段直接返回简单字典，不套统一响应结构
- Day 2 完成统一响应封装后，再决定是否把 /health 也纳入统一结构

面试考点：
- "你的服务怎么做健康检查？" → 这个接口就是答案
- "生产环境怎么监控服务状态？" → Docker healthcheck + /health 接口
"""

from fastapi import APIRouter

# APIRouter 是 FastAPI 的路由分组工具
# 每个模块创建自己的 router，然后在 router.py 中统一聚合
# 这样每个模块的路由定义独立，方便维护和测试
router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    健康检查接口

    返回服务名称和运行状态，用于探活验证。

    Returns:
        dict: 包含 status 和 service 字段的简单字典
    """
    return {
        "status": "ok",  # 服务运行正常
        "service": "supportforge-backend",  # 服务名称标识
    }
