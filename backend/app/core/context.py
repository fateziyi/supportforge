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

import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Optional

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


@dataclass(frozen=True)
class ContextTokens:
    """保存一次请求初始化时产生的 token，用于精确恢复原上下文。"""

    request_id: Token
    user_id: Token
    tenant_id: Token


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


def initialize_context(
    request_id: Optional[str] = None,
) -> tuple[str, ContextTokens]:
    """
    初始化一次请求的上下文，并保存进入请求前的状态。

    请求开始时先写入新的 request_id，同时把 user_id、tenant_id 置为未认证状态。
    返回的 token 必须在同一异步上下文中交给 reset_context()，以便在请求结束后
    恢复进入请求之前的值，而不是简单覆盖成 None。

    Args:
        request_id: 可选请求 ID；未提供时自动生成 UUID。

    Returns:
        tuple[str, ContextTokens]: 实际 request_id 与成对恢复所需的 token。
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    tokens = ContextTokens(
        request_id=request_id_ctx.set(request_id),
        user_id=user_id_ctx.set(None),
        tenant_id=tenant_id_ctx.set(None),
    )
    return request_id, tokens


def reset_context(tokens: ContextTokens) -> None:
    """
    恢复 initialize_context() 执行前的上下文状态。

    token 必须和 ContextVar 一一对应，并在创建 token 的同一异步上下文中使用。
    按写入的相反顺序恢复，便于未来扩展嵌套上下文字段时保持清晰的栈语义。

    Args:
        tokens: initialize_context() 返回的请求上下文 token 集合。
    """
    tenant_id_ctx.reset(tokens.tenant_id)
    user_id_ctx.reset(tokens.user_id)
    request_id_ctx.reset(tokens.request_id)


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


def set_user_id(user_id: Optional[str]) -> None:
    """写入已认证用户 ID，供同一请求内的审计和租户业务读取。"""
    user_id_ctx.set(user_id)


def get_tenant_id() -> Optional[str]:
    """
    获取当前用户所属的租户 ID

    Day 2 阶段返回 None（JWT 认证在 Week 2 实现）。

    Returns:
        Optional[str]: 当前租户 ID，可能为 None
    """
    return tenant_id_ctx.get()


def set_tenant_id(tenant_id: Optional[str]) -> None:
    """写入仅来自已认证用户的租户 ID，禁止用前端输入覆盖。"""
    tenant_id_ctx.set(tenant_id)


def clear_context() -> None:
    """
    强制清空所有上下文变量。

    该函数用于测试隔离或非请求场景的显式清理。HTTP 请求生命周期必须使用
    initialize_context() 与 reset_context() 成对管理，才能恢复嵌套调用前的值。

    为什么仍保留这个函数？
    - 单元测试可以在开始和结束时建立明确的空上下文
    - 命令行脚本等没有请求 token 的场景仍可显式清空
    - 兼容现有调用方，避免把强制清空和请求状态恢复混为一谈
    """
    request_id_ctx.set(None)
    user_id_ctx.set(None)
    tenant_id_ctx.set(None)
