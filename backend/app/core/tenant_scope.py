"""租户数据访问边界：将已认证用户转换为不可变 Tenant Scope。"""

from dataclasses import dataclass

from ..core.context import get_tenant_id, get_user_id
from ..core.exceptions import UnauthorizedException
from ..models.user import User


@dataclass(frozen=True)
class TenantScope:
    """仅由服务端已认证用户生成的租户访问范围。"""

    tenant_id: str
    user_id: str
    role: str


def scope_from_user(user: User) -> TenantScope:
    """从数据库已验证用户创建 scope，绝不接收前端 tenant_id。"""
    return TenantScope(tenant_id=user.tenant_id, user_id=user.id, role=user.role)


def get_required_tenant_scope(current_user: User) -> TenantScope:
    """确认请求上下文与当前用户一致后返回可用于 Repository 的 scope。"""
    if get_user_id() != current_user.id or get_tenant_id() != current_user.tenant_id:
        raise UnauthorizedException()
    return scope_from_user(current_user)
