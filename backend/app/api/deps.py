"""
全局依赖注入模块

这个文件定义了 FastAPI 路由中常用的公共依赖函数。
通过 Depends() 机制，路由处理函数可以自动获得数据库会话、当前用户等信息。

Day 1 阶段：get_db() 和 get_current_user() 都是占位实现
Day 3 阶段：get_db() 已从 db/session.py 导入真实实现
Week 2 阶段：get_current_user() 将实现 JWT 认证逻辑

为什么把依赖集中放在 deps.py？
- 所有路由需要的公共依赖统一在一个地方定义，避免每个路由文件重复代码
- 如果数据库会话的创建方式改变（比如加连接池参数），只需改 deps.py 的导入
- 认证逻辑改变时，也只需改 get_current_user() 的实现

使用方式（路由中的典型用法）：
    from fastapi import Depends
    from app.api.deps import get_db, get_current_user
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/tenants")
    async def list_tenants(
        db: AsyncSession = Depends(get_db),
        user = Depends(get_current_user),
    ):
        ...

面试考点：
- "FastAPI 的依赖注入是怎么用的？" → Depends() + yield 模式
- "get_db 为什么用 yield 而不是 return？" → 确保请求结束后 session 被关闭
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.context import set_tenant_id, set_user_id
from ..core.exceptions import UnauthorizedException
from ..core.security import decode_access_token

# 从 db/session.py 导入真实的 get_db 函数
# 不在 deps.py 里重复创建 engine/sessionmaker，保持单一事实来源
# 这样 db/session.py 是数据库基础设施的唯一定义处，deps.py 只做转发
from ..db.session import (
    get_db,  # noqa: F401 — 路由层通过 Depends(get_db) 使用，不在本文件内直接调用
)
from ..models.user import User
from ..repositories.user_repo import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    获取当前登录用户（占位实现）

    Week 2 实现 JWT 认证后，这个函数会：
    1. 从请求头中提取 Authorization: Bearer <token>
    2. 解析 JWT token，获取 user_id 和 tenant_id
    3. 从数据库查询用户信息，验证用户是否有效
    4. 将 tenant_id 写入 ContextVar（供多租户过滤使用）

    目前保留占位，确保导入时不会报错。
    """
    if credentials is None:
        raise UnauthorizedException()
    payload = decode_access_token(credentials.credentials)
    user = await UserRepository(db).get_active_by_id_and_tenant(
        payload.sub, payload.tenant_id
    )
    if user is None:
        raise UnauthorizedException()
    set_user_id(user.id)
    set_tenant_id(user.tenant_id)
    return user
