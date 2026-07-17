"""租户 API DTO：只暴露当前租户的必要公开信息。"""

from pydantic import BaseModel


class CurrentTenantResponse(BaseModel):
    """当前认证用户可见的租户信息。"""

    id: str
    name: str
    slug: str
    status: str
