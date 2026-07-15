"""
认证接口路由

这个文件定义了认证相关的 API 路由。
Day 8 将登录请求交给认证服务，返回真实 Access JWT。

设计说明：
- 路由层只做参数接收、依赖注入与响应返回，不承载认证业务逻辑
- AuthService 负责用户查询、账号状态校验、密码校验与 Access JWT 签发
- Day 8 只返回 Access Token；Refresh Token 与当前用户依赖留待 Day 9

面试考点：
- "登录路由为什么不查数据库？" → 路由只做协议层职责，业务放在 Service
- "JWT 如何承载多租户上下文？" → 仅从已验证用户写入 tenant_id、role 等 claims
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.auth import LoginRequest, TokenResponse
from ...schemas.common import ApiResponse
from ...services.auth_service import AuthService
from ..deps import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """
    登录接口。

    路由层只负责接收请求和返回统一响应；密码校验、账号状态判断和 JWT
    签发均下沉到 AuthService。tenant_id 不由前端传入，避免伪造租户身份。

    Args:
        payload: 包含邮箱和密码的登录请求。
        db: 当前请求的异步数据库会话。

    Returns:
        统一响应中的 TokenResponse，包含 Access Token 和用户公开信息。
    """
    token_response = await AuthService(db).authenticate(
        email=str(payload.email),
        password=payload.password,
    )
    return ApiResponse(data=token_response)
