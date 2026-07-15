"""Week 1 API 契约回归测试。"""

from app.main import app
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


def test_mock_login_and_error_response_are_stable() -> None:
    """Week 2 替换认证内部实现时，外部响应契约不能漂移。"""
    with TestClient(app) as client:
        success = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@acme.com", "password": "123456"},
        )
        failure = client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "123456"},
        )

    assert success.status_code == 200
    assert success.json()["code"] == 0
    assert success.json()["data"]["user"]["tenant_id"] == "default-tenant-id"
    assert failure.status_code == 401
    assert failure.json()["code"] == 40100
    assert failure.json()["data"] is None
