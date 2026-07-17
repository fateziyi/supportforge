"""租户服务：编排可信 scope 与当前租户查询。"""

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import NotFoundException
from ..core.tenant_scope import get_required_tenant_scope
from ..models.tenant import Tenant
from ..models.user import User
from ..repositories.tenant_repo import TenantRepository


class TenantService:
    """当前租户查询服务，路由层不得直接操作 ORM。"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_current_tenant(self, current_user: User) -> Tenant:
        """返回当前用户的活跃租户；无结果统一隐藏为资源不存在。"""
        scope = get_required_tenant_scope(current_user)
        tenant = await TenantRepository(self._session, scope).get_current_active()
        if tenant is None:
            raise NotFoundException()
        return tenant
