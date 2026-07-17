"""当前租户接口：验证 Tenant Scope 的最小受保护业务闭环。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.user import User
from ...schemas.common import ApiResponse
from ...schemas.tenant import CurrentTenantResponse
from ...services.tenant_service import TenantService
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/current", response_model=ApiResponse[CurrentTenantResponse])
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[CurrentTenantResponse]:
    """只返回认证用户所属租户，忽略任何前端试图指定的目标租户。"""
    tenant = await TenantService(db).get_current_tenant(current_user)
    return ApiResponse(
        data=CurrentTenantResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            status=tenant.status,
        )
    )
