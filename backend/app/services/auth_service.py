"""认证服务：编排用户查询、密码校验、状态检查与 JWT 签发。"""

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.exceptions import ForbiddenException, UnauthorizedException
from ..core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from ..models.user import User
from ..repositories.refresh_token_session_repo import RefreshTokenSessionRepository
from ..repositories.user_repo import UserRepository
from ..schemas.auth import CurrentUserResponse, TokenResponse


class AuthService:
    """登录业务服务，保持路由层不承载认证业务逻辑。"""

    def __init__(self, session: AsyncSession):
        """初始化仓储，确保数据访问仍集中在 Repository 层。"""
        self._session = session
        self._user_repository = UserRepository(session)
        self._refresh_session_repository = RefreshTokenSessionRepository(session)

    async def authenticate(
        self, *, email: str, password: str, tenant_slug: str | None = None
    ) -> TokenResponse:
        """校验登录凭据后返回 Access Token 与安全的用户公开信息。"""
        user = await self._user_repository.get_by_email_for_login(email, tenant_slug)
        if user is None:
            raise UnauthorizedException("邮箱或密码错误")

        if user.status != "active":
            raise ForbiddenException("用户已被禁用")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("邮箱或密码错误")

        return await self._issue_token_pair(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """轮换 Refresh Session 后签发新 token 对；旧 token 仅能成功使用一次。"""
        payload = decode_refresh_token(refresh_token)
        record = await self._refresh_session_repository.get_active_for_update(
            jti=payload.jti, user_id=payload.sub, tenant_id=payload.tenant_id
        )
        if record is None:
            raise UnauthorizedException()
        user = await self._user_repository.get_active_by_id_and_tenant(
            payload.sub, payload.tenant_id
        )
        if user is None:
            raise UnauthorizedException()
        new_refresh_token, new_refresh_payload = create_refresh_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role
        )
        await self._refresh_session_repository.revoke(
            record, reason="rotated", replaced_by_jti=new_refresh_payload.jti
        )
        await self._refresh_session_repository.create(
            user_id=user.id,
            tenant_id=user.tenant_id,
            jti=new_refresh_payload.jti,
            expires_at=new_refresh_payload.exp,
        )
        await self._session.commit()
        return self._build_token_response(user, new_refresh_token)

    async def logout(self, *, user_id: str, tenant_id: str) -> None:
        """撤销当前用户在当前租户的所有 Refresh Session。"""
        await self._refresh_session_repository.revoke_all_for_user(
            user_id=user_id, tenant_id=tenant_id
        )
        await self._session.commit()

    async def _issue_token_pair(self, user: User) -> TokenResponse:
        """为已校验用户创建 Refresh Session 并返回完整 token 对。"""
        refresh_token, refresh_payload = create_refresh_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role
        )
        await self._refresh_session_repository.create(
            user_id=user.id,
            tenant_id=user.tenant_id,
            jti=refresh_payload.jti,
            expires_at=refresh_payload.exp,
        )
        await self._session.commit()
        return self._build_token_response(user, refresh_token)

    def _build_token_response(self, user: User, refresh_token: str) -> TokenResponse:
        """仅构造 API DTO，避免路由层拼接 token 和用户公开字段。"""
        access_token = create_access_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user=CurrentUserResponse(
                id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                role=user.role,
            ),
        )
