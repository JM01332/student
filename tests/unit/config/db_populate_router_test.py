"""ADMIN-Schutz des Dev-Routers ohne Datenbank und Keycloak prüfen."""

import asyncio
from http import HTTPStatus
lazy from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI
lazy from pytest_mock import MockerFixture

from student.config.dev.db_populate import DbPopulateService, get_db_populate_service
from student.config.dev.db_populate_router import router
from student.fastapi_app import authorization_error_handler
from student.security import AuthorizationError, Role, TokenService, User
from student.security.dependencies import get_token_service


@pytest.fixture
def service(mocker: MockerFixture) -> Mock:
    """DB-Neuladen durch eine Attrappe ersetzen."""
    return mocker.Mock(spec=DbPopulateService)


@pytest.fixture
def app(service: Mock, mocker: MockerFixture) -> FastAPI:
    """Echte Rollen- und Bearer-Prüfung mit synthetischen Token-Benutzern."""
    app = FastAPI()
    app.include_router(router, prefix="/dev")
    app.exception_handler(AuthorizationError)(authorization_error_handler)
    token_service = TokenService.__new__(TokenService)

    def decode(token: str) -> User:
        users = {
            "admin": [Role.ADMIN],
            "both": [Role.STUDENT, Role.ADMIN],
            "student": [Role.STUDENT],
            "none": [],
        }
        if token not in users:
            raise AuthorizationError
        return User(
            username="test",
            email="test@example.org",
            vorname="Test",
            nachname="Test",
            roles=users[token],
        )

    mocker.patch.object(token_service, "get_user_from_token", side_effect=decode)
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_db_populate_service] = lambda: service
    return app


def _query(
    app: FastAPI, authorization: str | None, body: bytes = b""
) -> httpx.Response:
    """ASGI-Request ohne laufende Dienste senden."""
    headers = {} if authorization is None else {"Authorization": authorization}

    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client:
            return await client.request(
                "QUERY", "/dev/db_populate", headers=headers, content=body
            )

    return asyncio.run(send())


@pytest.mark.parametrize("body", [b"", b"{}"])
@pytest.mark.parametrize(
    "authorization", [None, "Basic admin", "Bearer", "Bearer invalid"]
)
def test_requires_valid_bearer(
    app: FastAPI, service: Mock, authorization: str | None, body: bytes
) -> None:
    response = _query(app, authorization, body)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["content-type"] == "application/problem+json"
    assert service.mock_calls == []


@pytest.mark.parametrize("body", [b"", b"{}"])
@pytest.mark.parametrize("role", ["student", "none"])
def test_requires_admin(app: FastAPI, service: Mock, role: str, body: bytes) -> None:
    response = _query(app, f"Bearer {role}", body)
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert service.mock_calls == []


@pytest.mark.parametrize("role", ["admin", "both"])
def test_admin_populates(app: FastAPI, service: Mock, role: str) -> None:
    response = _query(app, f"Bearer {role}")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"db_populate": "success"}
    service.populate.assert_called_once_with()


def test_admin_requires_empty_body(app: FastAPI, service: Mock) -> None:
    response = _query(app, "Bearer admin", b"{}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status_code"] == HTTPStatus.BAD_REQUEST
    assert service.mock_calls == []
