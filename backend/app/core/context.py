"""
请求级上下文管理模块

这个文件使用 Python 的 ContextVar 机制，在单个请求的生命周期内
保存和传递上下文信息（request_id、user_id、tenant_id）。

什么是 ContextVar？
- Python 3.7+ 提供的"上下文变量"机制
- 类似于"线程局部变量"，但支持 asyncio 异步场景
- 每个请求有自己的上下文副本，请求之间不会互相干扰
- 请求结束后，上下文自动清理，不会串数据

为什么需要请求上下文？
- 日志需要 request_id：方便把同一个请求的所有日志串联起来排查
- 多租户需要 tenant_id：确保数据库查询自动过滤当前租户的数据
- 审计需要 user_id：记录"谁做了什么操作"
- 这些信息在请求进入时注入，后续所有模块直接读取，不需要层层传参

使用方式：
    # 设置上下文（通常在中间件中自动设置，不需要手动调用）
    from app.core.context import set_request_id
    set_request_id("abc-123")

    # 读取上下文（在任何模块中都可以读取）
    from app.core.context import get_request_id
    rid = get_request_id()  # → "abc-123"

    # 清理上下文（请求结束时自动清理）
    from app.core.context import clear_context
    clear_context()

面试考点：
- "你的多租户上下文是怎么传递的？" → ContextVar，不需要每个函数都传 tenant_id 参数
- "为什么不用全局变量？" → 全局变量会被多个请求共享，ContextVar 每个请求独立
"""

from contextvars import ContextVar
from typing import Optional
import uuid


# ── 定义三个上下文变量 ──
# ContextVar 的第一个参数是名称，default 是默认值（请求开始前为 None）

# request_id: 每个请求的唯一标识，用于日志串联和问题排查
# 由 RequestLogMiddleware 在请求进入时自动生成（Day 2）
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# user_id: 当前登录用户的 ID
# Week 2 实现 JWT 后，从 token 中解析并注入
user_id_ctx: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

# tenant_id: 当前用户所属的租户 ID
# Week 2 实现 JWT 后，从 token 中解析并注入
# ⚠️ 重要：tenant_id 只从 JWT 解析，不信任前端传参（CLAUDE.md 规则）
tenant_id_ctx: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)


# ── 便捷函数 ──
# 提供 getter/setter，不直接操作底层 ContextVar
# 这样如果以后需要加日志或校验，只需要改这些函数即可

def set_request_id(request_id: Optional[str] = None) -> str:
    """
    设置当前请求的 request_id

    如果没有传入 request_id，会自动生成一个 UUID。
    通常在 RequestLogMiddleware 中调用。

    Args:
        request_id: 可选的请求 ID，如果不传则自动生成

    Returns:
        str: 实际使用的 request_id
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_ctx.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """
    获取当前请求的 request_id

    如果请求还没开始（比如在非请求上下文中调用），返回 None。

    Returns:
        Optional[str]: 当前请求的 request_id，可能为 None
    """
    return request_id_ctx.get()


def get_user_id() -> Optional[str]:
    """
    获取当前登录用户的 ID

    Day 2 阶段返回 None（JWT 认证在 Week 2 实现）。

    Returns:
        Optional[str]: 当前用户的 ID，可能为 None
    """
    return user_id_ctx.get()


def get_tenant_id() -> Optional[str]:
    """
    获取当前用户所属的租户 ID

    Day 2 阶段返回 None（JWT 认证在 Week 2 实现）。

    Returns:
        Optional[str]: 当前租户 ID，可能为 None
    """
    return tenant_id_ctx.get()


def clear_context() -> None:
    """
    清理所有上下文变量

    在请求结束时调用，防止上下文数据在下一个请求中被误读。
    通常在 RequestLogMiddleware 的 finally 块中调用。

    为什么需要清理？
    - ContextVar 的值会在请求结束后"残留"
    - 如果不清理，下一个请求可能读到上一个请求的数据
    - 这在多租户场景下尤其危险：可能导致跨租户数据泄露
    """
    request_id_ctx.set(None)
    user_id_ctx.set(None)
    tenant_id_ctx.set(None)