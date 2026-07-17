"""请求上下文生命周期测试。"""

from collections.abc import Generator

import pytest
from app.core.context import (
    clear_context,
    get_request_id,
    get_tenant_id,
    get_user_id,
    initialize_context,
    reset_context,
    set_request_id,
    set_tenant_id,
    set_user_id,
)
from app.core.logging import RequestLogMiddleware
from starlette.requests import Request


@pytest.fixture(autouse=True)
def isolate_context() -> Generator[None, None, None]:
    """每个测试前后强制清空上下文，避免测试之间互相影响。"""
    clear_context()
    yield
    clear_context()


def test_reset_context_restores_outer_values() -> None:
    """嵌套请求上下文结束后，应恢复进入请求前的值而不是统一置空。"""
    set_request_id("outer-request")
    set_user_id("outer-user")
    set_tenant_id("outer-tenant")

    request_id, tokens = initialize_context("inner-request")
    assert request_id == "inner-request"
    assert get_request_id() == "inner-request"
    assert get_user_id() is None
    assert get_tenant_id() is None

    set_user_id("inner-user")
    set_tenant_id("inner-tenant")
    reset_context(tokens)

    assert get_request_id() == "outer-request"
    assert get_user_id() == "outer-user"
    assert get_tenant_id() == "outer-tenant"


@pytest.mark.asyncio
async def test_middleware_restores_context_when_downstream_raises() -> None:
    """下游抛出异常时，中间件的 finally 仍应恢复原上下文。"""
    set_request_id("outer-request")
    set_user_id("outer-user")
    set_tenant_id("outer-tenant")

    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/raise-error",
            "root_path": "",
            "query_string": b"",
            "headers": [],
            "client": ("test-client", 123),
            "server": ("test-server", 80),
        }
    )

    async def unused_app(scope, receive, send) -> None:
        """满足中间件构造函数要求；本测试直接调用 dispatch，不会执行该函数。"""

    middleware = RequestLogMiddleware(app=unused_app)

    async def raise_error(request: Request):
        set_user_id("inner-user")
        set_tenant_id("inner-tenant")
        raise RuntimeError("downstream failed")

    with pytest.raises(RuntimeError, match="downstream failed"):
        await middleware.dispatch(request, raise_error)

    assert get_request_id() == "outer-request"
    assert get_user_id() == "outer-user"
    assert get_tenant_id() == "outer-tenant"
