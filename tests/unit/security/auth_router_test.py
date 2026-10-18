"""Login-Requests gegen die Anwendung ohne Keycloak oder DB-Start prüfen."""

import asyncio
from http import HTTPStatus
from unittest.mock import Mock

import httpx
import pytest

from student.fastapi_app import app
from student.security import AuthorizationError, LoginError, Role, TokenService, User
from student.security.dependencies import get_token_service
from student.security.login_data import LoginData

TEST_PASSWORD = "test-password"  # ruff: ignore[hardcoded-password-string] -- ausschließlich Testdaten
TEST_TOKEN = "test-access-token"  # ruff: ignore[hardcoded-password-string] -- ausschließlich Testdaten


@pytest.fixture
def service():
    """TokenService ersetzen; ASGITransport führt keinen Lifespan aus."""
    mock = Mock(spec=TokenService)
    mock.token.return_value = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "expires_in": 1800,
    }
    mock.get_user_from_token.return_value = User(
        username="admin",
        email="admin@example.org",
        nachname="Test",
        vorname="Admin",
        roles=[Role.ADMIN, Role.STUDENT],
    )
    app.dependency_overrides[get_token_service] = lambda: mock
    try:
        yield mock
    finally:
        del app.dependency_overrides[get_token_service]


def _request(body: bytes, method: str = "QUERY") -> httpx.Response:
    """HTTP-Request mit echtem Routing und Middleware ausführen."""

    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client:
            return await client.request(
                method,
                "/auth/token",
                content=body,
                headers={"Content-Type": "application/json"},
            )

    return asyncio.run(send())


def test_login(service: Mock) -> None:
    response = _request(b'{"username":"admin","password":"test-password"}')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "token": "test-access-token",
        "expires_in": 1800,
        "rollen": ["ADMIN", "STUDENT"],
    }
    service.token.assert_called_once_with(username="admin", password=TEST_PASSWORD)
    service.get_user_from_token.assert_called_once_with(token=TEST_TOKEN)


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"{",
        b"\xff",
        b"null",
        b"[]",
        b'"text"',
        b"1",
        b"true",
        b"{}",
        b'{"username":"admin"}',
        b'{"password":"test-password"}',
        b'{"username":"admin","password":"test-password","extra":true}',
    ],
)
def test_invalid_body(service: Mock, body: bytes) -> None:
    response = _request(body)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.content == b""
    service.token.assert_not_called()
    service.get_user_from_token.assert_not_called()


def test_login_rejected(service: Mock) -> None:
    service.token.side_effect = LoginError(username="admin")
    response = _request(b'{"username":"admin","password":"wrong"}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Unauthorized"
    service.get_user_from_token.assert_not_called()


def test_invalid_token(service: Mock) -> None:
    service.get_user_from_token.side_effect = AuthorizationError
    response = _request(b'{"username":"admin","password":"test-password"}')
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {
        "title": "Unauthorized",
        "status_code": 401,
        "detail": None,
    }
    assert "test-access-token" not in response.text


def test_post_not_supported(service: Mock) -> None:
    assert _request(b"{}", method="POST").status_code == HTTPStatus.METHOD_NOT_ALLOWED
    service.token.assert_not_called()


def test_password_not_in_repr() -> None:
    data = LoginData(username="admin", password=TEST_PASSWORD)
    assert "test-password" not in repr(data)
