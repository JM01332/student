"""ADMIN-Schutz des Routers zum Neuladen von Keycloak ohne laufende Dienste prüfen."""

import asyncio
from http import HTTPStatus
lazy from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI
lazy from pytest_mock import MockerFixture

from student.config.dev.keycloak_populate import (
    KeycloakPopulateService,
    get_keycloak_populate_service,
)
from student.config.dev.keycloak_populate_router import router
from student.fastapi_app import authorization_error_handler
from student.security import AuthorizationError, Role, TokenService, User
from student.security.dependencies import get_token_service


@pytest.fixture
def service(mocker: MockerFixture) -> Mock:
    """Keycloak-Neuladen durch eine Attrappe ersetzen."""
    return mocker.Mock(spec=KeycloakPopulateService)


@pytest.fixture
def app(service: Mock, mocker: MockerFixture) -> FastAPI:
    """Echte Rollen- und Bearer-Prüfung mit synthetischen Token-Benutzern."""
    app = FastAPI()
    app.include_router(router, prefix="/dev")
    app.exception_handler(AuthorizationError)(authorization_error_handler)
    token_service = TokenService.__new__(TokenService)

    def decode(token: str) -> User:
        users = {"admin": [Role.ADMIN], "student": [Role.STUDENT]}
        if token not in users:
            raise AuthorizationError
        return User(
            username=token,
            email="test@example.org",
            vorname="Test",
            nachname="Test",
            roles=users[token],
        )

    mocker.patch.object(token_service, "get_user_from_token", side_effect=decode)
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_keycloak_populate_service] = lambda: service
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
                "QUERY", "/dev/keycloak_populate", headers=headers, content=body
            )

    return asyncio.run(send())


@pytest.mark.parametrize(
    ("authorization", "status_code"),
    [
        (None, HTTPStatus.UNAUTHORIZED),
        ("Bearer invalid", HTTPStatus.UNAUTHORIZED),
        ("Bearer student", HTTPStatus.FORBIDDEN),
    ],
)
def test_nur_admin(
    app: FastAPI, service: Mock, authorization: str | None, status_code: HTTPStatus
) -> None:
    """Ohne gültiges Token 401, ohne Rolle admin 403; Keycloak bleibt unberührt."""
    response = _query(app, authorization)
    assert response.status_code == status_code
    assert service.mock_calls == []


def test_admin_populates(app: FastAPI, service: Mock) -> None:
    response = _query(app, "Bearer admin")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"keycloak_populate": "success"}
    service.populate.assert_called_once_with()


def test_admin_requires_empty_body(app: FastAPI, service: Mock) -> None:
    response = _query(app, "Bearer admin", b"{}")
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.headers["content-type"] == "application/problem+json"
    assert service.mock_calls == []
