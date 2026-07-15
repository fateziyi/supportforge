"""认证服务：编排用户查询、密码校验、状态检查与 JWT 签发。"""

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.exceptions import ForbiddenException, UnauthorizedException
from ..core.security import create_access_token, verify_password
from ..repositories.user_repo import UserRepository
from ..schemas.auth import CurrentUserResponse, TokenResponse


class AuthService:
    """登录业务服务，保持路由层不承载认证业务逻辑。"""

    def __init__(self, session: AsyncSession):
        """初始化仓储，确保数据访问仍集中在 Repository 层。"""
        self._user_repository = UserRepository(session)

    async def authenticate(self, *, email: str, password: str) -> TokenResponse:
        """校验登录凭据后返回 Access Token 与安全的用户公开信息。"""
        user = await self._user_repository.get_by_email_for_login(email)
        if user is None:
            raise UnauthorizedException("邮箱或密码错误")

        if user.status != "active":
            raise ForbiddenException("用户已被禁用")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("邮箱或密码错误")

        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token="",
            expires_in=settings.access_token_expire_minutes * 60,
            user=CurrentUserResponse(
                id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                role=user.role,
            ),
        )
