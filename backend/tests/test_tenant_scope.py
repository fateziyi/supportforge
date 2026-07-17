"""Day 10 Tenant Scope 单元测试。"""

from types import SimpleNamespace

import pytest
from app.core.context import clear_context, set_tenant_id, set_user_id
from app.core.exceptions import UnauthorizedException
from app.core.tenant_scope import get_required_tenant_scope, scope_from_user
from app.models.knowledge_base import KnowledgeBase
from app.repositories.base import TenantScopedRepository


def test_scope_only_comes_from_authenticated_user() -> None:
    """Scope 的用户、租户与角色必须来自服务端 User 对象。"""
    user = SimpleNamespace(id="user-a", tenant_id="tenant-a", role="tenant_admin")

    scope = scope_from_user(user)

    assert scope.tenant_id == "tenant-a"
    assert scope.user_id == "user-a"
    assert scope.role == "tenant_admin"


def test_required_scope_rejects_missing_or_mismatched_context() -> None:
    """请求上下文未由认证依赖注入时，不能进入租户数据访问层。"""
    user = SimpleNamespace(id="user-a", tenant_id="tenant-a", role="tenant_admin")
    clear_context()
    with pytest.raises(UnauthorizedException):
        get_required_tenant_scope(user)

    set_user_id("user-a")
    set_tenant_id("tenant-a")
    assert get_required_tenant_scope(user).tenant_id == "tenant-a"
    clear_context()


def test_scoped_repository_statement_always_contains_tenant_filter() -> None:
    """资源 ID 查询必须同时带上当前 Tenant Scope，防止跨租户命中。"""
    scope = scope_from_user(
        SimpleNamespace(id="user-a", tenant_id="tenant-a", role="tenant_admin")
    )
    repository = TenantScopedRepository(session=object(), scope=scope)

    statement = repository.build_scoped_id_statement(KnowledgeBase, "kb-other")
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))

    assert "knowledge_bases.tenant_id" in compiled
    assert "tenant-a" in compiled
