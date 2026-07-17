"""租户仓储基类：为后续业务资源提供不可省略的 tenant_id 查询条件。"""

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.tenant_scope import TenantScope


class TenantScopedRepository:
    """所有租户业务 Repository 的基类，不提供无 scope 的资源读取接口。"""

    def __init__(self, session: AsyncSession, scope: TenantScope):
        self._session = session
        self._scope = scope

    def build_scoped_id_statement(
        self, model: type[Any], resource_id: str
    ) -> Select[Any]:
        """构造同时匹配资源 ID 与当前 scope tenant_id 的查询语句。"""
        return select(model).where(
            model.id == resource_id,
            model.tenant_id == self._scope.tenant_id,
        )

    async def get_by_id(self, model: type[Any], resource_id: str) -> Any | None:
        """按资源 ID 读取当前租户资源；他租户资源与不存在资源均返回 None。"""
        result = await self._session.execute(
            self.build_scoped_id_statement(model, resource_id)
        )
        return result.scalar_one_or_none()
