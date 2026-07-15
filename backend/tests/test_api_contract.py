"""API 统一响应契约回归测试。"""

import pytest
from app.api.deps import get_db
from app.core.exceptions import UnauthorizedException
from app.main import app
from app.schemas.auth import CurrentUserResponse, TokenResponse
from app.services.auth_service import AuthService
from fastapi.testclient import TestClient


def test_health_uses_standard_response_envelope() -> None:
    """健康检查也必须遵守统一顶层响应结构。"""
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "code": 0,
        "message": "success",
        "data": {"status": "ok", "service": "supportforge-backend"},
    }


def test_login_and_error_response_are_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    """认证实现替换后，外部接口的成功和失败响应契约不能漂移。"""

    async def override_db():
        yield object()

    async def fake_authenticate(
        self: AuthService,
        *,
        email: str,
        password: str,
    ) -> TokenResponse:
        if email != "admin@acme.com":
            raise UnauthorizedException("邮箱或密码错误")
        return TokenResponse(
            access_token="test-access-token",
            refresh_token="",
            expires_in=1800,
            user=CurrentUserResponse(
                id="default-admin-id",
                tenant_id="default-tenant-id",
                email=email,
                role="tenant_admin",
            ),
        )

    monkeypatch.setattr(AuthService, "authenticate", fake_authenticate)
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            success = client.post(
                "/api/v1/auth/login",
                json={"email": "admin@acme.com", "password": "123456"},
            )
            failure = client.post(
                "/api/v1/auth/login",
                json={"email": "wrong@example.com", "password": "123456"},
            )
    finally:
        app.dependency_overrides.clear()

    assert success.status_code == 200
    assert success.json()["code"] == 0
    assert success.json()["data"]["user"]["tenant_id"] == "default-tenant-id"
    assert failure.status_code == 401
    assert failure.json()["code"] == 40100
    assert failure.json()["data"] is None


def test_validation_error_without_json_content_type_uses_422_envelope() -> None:
    """原始请求体触发校验失败时，也不能因 bytes 序列化问题变成 500。"""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            content=b'{"email":"admin@acme.com","password":"123456"}',
        )

    assert response.status_code == 422
    assert response.json()["code"] == 42200
    assert response.json()["data"] is not None
