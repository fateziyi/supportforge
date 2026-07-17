"""租户仓储：读取时始终约束为当前认证用户所属租户。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.tenant_scope import TenantScope
from ..models.tenant import Tenant


class TenantRepository:
    """当前租户的数据访问入口。"""

    def __init__(self, session: AsyncSession, scope: TenantScope):
        self._session = session
        self._scope = scope

    async def get_current_active(self) -> Tenant | None:
        """读取 scope 对应的活跃租户，不接受调用方提供的目标 tenant_id。"""
        result = await self._session.execute(
            select(Tenant).where(
                Tenant.id == self._scope.tenant_id,
                Tenant.status == "active",
            )
        )
        return result.scalar_one_or_none()
