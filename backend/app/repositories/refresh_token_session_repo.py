"""Refresh Token 会话仓储：只负责持久化与行锁，不处理 JWT。"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.refresh_token_session import RefreshTokenSession


class RefreshTokenSessionRepository:
    """封装 Refresh Session 的创建、锁定查询与撤销。"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, *, user_id: str, tenant_id: str, jti: str, expires_at: datetime
    ) -> RefreshTokenSession:
        """创建活动会话；调用方在同一事务中负责提交。"""
        record = RefreshTokenSession(
            id=str(uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            jti=jti,
            expires_at=expires_at,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_active_for_update(
        self, *, jti: str, user_id: str, tenant_id: str
    ) -> RefreshTokenSession | None:
        """加行锁读取未撤销且未过期的会话，确保同一 token 仅能轮换一次。"""
        result = await self._session.execute(
            select(RefreshTokenSession)
            .where(
                RefreshTokenSession.jti == jti,
                RefreshTokenSession.user_id == user_id,
                RefreshTokenSession.tenant_id == tenant_id,
                RefreshTokenSession.revoked_at.is_(None),
                RefreshTokenSession.expires_at > datetime.now(timezone.utc),
            )
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def revoke(
        self,
        record: RefreshTokenSession,
        *,
        reason: str,
        replaced_by_jti: str | None = None,
    ) -> None:
        """撤销指定会话，并记录轮换链路。"""
        record.revoked_at = datetime.now(timezone.utc)
        record.revoked_reason = reason
        record.replaced_by_jti = replaced_by_jti
        await self._session.flush()

    async def revoke_all_for_user(self, *, user_id: str, tenant_id: str) -> None:
        """登出时撤销当前用户当前租户的全部未撤销会话。"""
        await self._session.execute(
            update(RefreshTokenSession)
            .where(
                RefreshTokenSession.user_id == user_id,
                RefreshTokenSession.tenant_id == tenant_id,
                RefreshTokenSession.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc), revoked_reason="logout")
        )
