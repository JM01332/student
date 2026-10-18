"""Rollenprüfung und ihre FastAPI-Einbindung ohne externe Dienste prüfen."""

import asyncio
from http import HTTPStatus
from unittest.mock import Mock

import httpx
import pytest
from fastapi import Depends, FastAPI, HTTPException, Request

from student.fastapi_app import authorization_error_handler
from student.security import AuthorizationError, Role, RolesRequired, TokenService, User
from student.security.dependencies import get_token_service


def _service(roles: list[Role]) -> Mock:
    """TokenService mit bereits authentifiziertem Testbenutzer bereitstellen."""
    service = Mock(spec=TokenService)
    service.get_user_from_request.return_value = User(
        username="test",
        email="test@example.org",
        nachname="Test",
        vorname="Test",
        roles=roles,
    )
    return service


@pytest.mark.parametrize(
    ("required", "roles"),
    [
        (Role.ADMIN, [Role.ADMIN]),
        (Role.STUDENT, [Role.ADMIN, Role.STUDENT]),
        ([Role.ADMIN], [Role.ADMIN]),
        ([Role.ADMIN, Role.STUDENT], [Role.STUDENT]),
        ([Role.ADMIN, Role.STUDENT], [Role.ADMIN]),
        ([Role.STUDENT], [Role.ADMIN, Role.STUDENT]),
    ],
)
def test_matching_role(required: list[Role] | Role, roles: list[Role]) -> None:
    request = Request({"type": "http"})
    service = _service(roles)
    assert RolesRequired(required)(request, service) is None
    assert request.state.current_user is service.get_user_from_request.return_value
    service.get_user_from_request.assert_called_once_with(request)


@pytest.mark.parametrize(
    ("required", "roles"),
    [
        (Role.ADMIN, [Role.STUDENT]),
        (Role.STUDENT, [Role.ADMIN]),
        (Role.ADMIN, []),
        ([Role.ADMIN], [Role.STUDENT]),
        ([Role.ADMIN, Role.STUDENT], []),
        ([], [Role.ADMIN, Role.STUDENT]),
        ([], []),
    ],
)
def test_missing_role(required: list[Role] | Role, roles: list[Role]) -> None:
    request = Request({"type": "http"})
    service = _service(roles)
    with pytest.raises(HTTPException) as exc_info:
        RolesRequired(required)(request, service)
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert not hasattr(request.state, "current_user")
    service.get_user_from_request.assert_called_once_with(request)


def test_authorization_error_propagates() -> None:
    request = Request({"type": "http"})
    service = _service([])
    error = AuthorizationError()
    service.get_user_from_request.side_effect = error
    with pytest.raises(AuthorizationError) as exc_info:
        RolesRequired(Role.ADMIN)(request, service)
    assert exc_info.value is error
    assert not hasattr(request.state, "current_user")


@pytest.mark.parametrize(
    ("roles", "invalid_token", "expected"),
    [
        ([Role.ADMIN], False, HTTPStatus.OK),
        ([Role.STUDENT], False, HTTPStatus.FORBIDDEN),
        ([], True, HTTPStatus.UNAUTHORIZED),
    ],
)
def test_dependency_in_fastapi(
    roles: list[Role], *, invalid_token: bool, expected: HTTPStatus
) -> None:
    app = FastAPI()
    app.exception_handler(AuthorizationError)(authorization_error_handler)
    service = _service(roles)
    if invalid_token:
        service.get_user_from_request.side_effect = AuthorizationError
    app.dependency_overrides[get_token_service] = lambda: service
    endpoint = Mock()

    @app.get("/protected", dependencies=[Depends(RolesRequired(Role.ADMIN))])
    def protected(request: Request) -> dict[str, str]:
        endpoint()
        assert request.state.current_user is service.get_user_from_request.return_value
        return {"username": request.state.current_user.username}

    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client:
            return await client.get("/protected")

    response = asyncio.run(send())
    assert response.status_code == expected
    service.get_user_from_request.assert_called_once()
    if expected == HTTPStatus.OK:
        endpoint.assert_called_once()
        assert response.json() == {"username": "test"}
    else:
        endpoint.assert_not_called()
        if expected == HTTPStatus.UNAUTHORIZED:
            assert response.headers["content-type"] == "application/problem+json"
        else:
            assert response.json() == {"detail": "Forbidden"}
