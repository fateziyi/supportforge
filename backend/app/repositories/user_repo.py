"""用户仓储：封装认证场景下的用户查询，避免 Service 直接拼接 SQL。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.tenant import Tenant
from ..models.user import User


class UserRepository:
    """用户数据访问入口。"""

    def __init__(self, session: AsyncSession):
        """保存由 FastAPI 依赖注入提供的异步数据库会话。"""
        self._session = session

    async def get_by_email_for_login(
        self, email: str, tenant_slug: str | None = None
    ) -> User | None:
        """按邮箱查找登录用户；跨租户同邮箱时拒绝选择任一账号。"""
        statement = select(User).where(User.email == email)
        if tenant_slug is not None:
            statement = statement.join(Tenant).where(Tenant.slug == tenant_slug)
        result = await self._session.execute(statement.limit(2))
        users = list(result.scalars())
        if len(users) > 1:
            # Day 8 还没有租户选择入口，不能静默挑选任意一个同邮箱账号；
            # 同时按普通认证失败返回，避免对外泄露账号配置或存在状态。
            return None
        return users[0] if users else None

    async def get_active_by_id_and_tenant(
        self, user_id: str, tenant_id: str
    ) -> User | None:
        """以 JWT 的主体和租户双条件回查活跃用户与活跃租户。"""
        result = await self._session.execute(
            select(User)
            .join(Tenant)
            .where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.status == "active",
                Tenant.status == "active",
            )
        )
        return result.scalar_one_or_none()
