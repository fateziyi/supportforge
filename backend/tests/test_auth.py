"""Day 8 认证核心逻辑测试，不依赖外部 PostgreSQL 服务。"""

from datetime import timedelta
from types import SimpleNamespace

import jwt
import pytest
from app.core.config import settings
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.auth_service import AuthService


def test_argon2_password_hash_can_only_verify_correct_password() -> None:
    """密码不以明文保存，且错误密码不能通过校验。"""
    password_hash = hash_password("123456")

    assert password_hash.startswith("$argon2")
    assert verify_password("123456", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_access_token_contains_required_claims() -> None:
    """签发出的 Access Token 必须携带用户、租户、角色与类型信息。"""
    token = create_access_token(
        user_id="user-1",
        tenant_id="tenant-1",
        role="tenant_admin",
    )

    payload = decode_access_token(token)

    assert payload.sub == "user-1"
    assert payload.tenant_id == "tenant-1"
    assert payload.role == "tenant_admin"
    assert payload.token_type == "access"


def test_invalid_or_expired_token_is_rejected() -> None:
    """篡改、过期或非 Access 类型的 token 都必须统一返回未认证错误。"""
    expired_token = create_access_token(
        user_id="user-1",
        tenant_id="tenant-1",
        role="tenant_admin",
        expires_delta=timedelta(seconds=-1),
    )
    refresh_like_token = jwt.encode(
        {
            "sub": "user-1",
            "tenant_id": "tenant-1",
            "role": "tenant_admin",
            "token_type": "refresh",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    for token in (expired_token, f"{expired_token}tampered", refresh_like_token):
        with pytest.raises(UnauthorizedException):
            decode_access_token(token)


@pytest.mark.asyncio
async def test_auth_service_returns_token_for_active_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """活跃用户的正确密码能够获得真实 JWT，而不是 mock token。"""
    user = SimpleNamespace(
        id="user-1",
        tenant_id="tenant-1",
        email="agent@example.com",
        role="support_agent",
        status="active",
        password_hash=hash_password("123456"),
    )

    async def fake_get_by_email(self: object, email: str) -> object:
        return user if email == user.email else None

    monkeypatch.setattr(
        "app.services.auth_service.UserRepository.get_by_email_for_login",
        fake_get_by_email,
    )
    response = await AuthService(session=None).authenticate(
        email=user.email,
        password="123456",
    )

    assert response.refresh_token == ""
    assert decode_access_token(response.access_token).tenant_id == "tenant-1"


@pytest.mark.asyncio
async def test_auth_service_rejects_unknown_email_bad_password_and_disabled_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """错误密码与禁用账号必须映射为规范定义的 401/403 业务异常。"""
    active_user = SimpleNamespace(
        id="user-1",
        tenant_id="tenant-1",
        email="agent@example.com",
        role="support_agent",
        status="active",
        password_hash=hash_password("123456"),
    )
    disabled_user = SimpleNamespace(**{**active_user.__dict__, "status": "disabled"})

    async def active_lookup(self: object, email: str) -> object:
        return active_user if email == active_user.email else None

    monkeypatch.setattr(
        "app.services.auth_service.UserRepository.get_by_email_for_login",
        active_lookup,
    )
    with pytest.raises(UnauthorizedException, match="邮箱或密码错误"):
        await AuthService(session=None).authenticate(
            email="unknown@example.com",
            password="bad",
        )
    with pytest.raises(UnauthorizedException, match="邮箱或密码错误"):
        await AuthService(session=None).authenticate(
            email=active_user.email,
            password="bad",
        )

    async def disabled_lookup(self: object, email: str) -> object:
        return disabled_user

    monkeypatch.setattr(
        "app.services.auth_service.UserRepository.get_by_email_for_login",
        disabled_lookup,
    )
    with pytest.raises(ForbiddenException, match="用户已被禁用"):
        await AuthService(session=None).authenticate(
            email=disabled_user.email,
            password="123456",
        )
