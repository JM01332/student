"""Unit-Tests für bedingte GET-Requests und Suchparameter ohne Datenbank."""

import asyncio
import json
from decimal import Decimal
from http import HTTPStatus
lazy from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI, Request
lazy from pytest_mock import MockerFixture

from student.fastapi_app import (
    authorization_error_handler,
    forbidden_error_handler,
    not_found_error_handler,
)
from student.router.dependencies import get_service
from student.router.student_find_model import StudentFindModel
from student.router.student_router import get, get_by_id, student_router
from student.security import AuthorizationError, Role, TokenService, User
from student.security.dependencies import get_token_service
from student.service import PruefungsleistungDTO, StudentDTO, StudentService
from student.service.exceptions import ForbiddenError, NotFoundError


@pytest.fixture
def service(mocker: MockerFixture) -> Mock:
    """Service-Attrappe mit einer Version ungleich null und einer Decimal-Note."""
    mock = mocker.Mock(spec=StudentService)
    mock.find_by_id.return_value = StudentDTO(
        id=1,
        version=3,
        matrikelnummer="123456",
        nachname="Mustermann",
        vorname="Max",
        email="max@example.org",
        username="max",
        adresse=None,
        pruefungsleistungen=[
            PruefungsleistungDTO(modul="Test", note=Decimal("1.3"), semester="SS 2026"),
        ],
    )
    return mock


def _request(etag: str | None) -> Request:
    """Request mit optionalem If-None-Match-Header erzeugen."""
    headers = [] if etag is None else [(b"if-none-match", etag.encode("ascii"))]
    request = Request({"type": "http", "headers": headers})
    request.state.current_user = User(
        username="test",
        email="test@example.org",
        vorname="Test",
        nachname="Test",
        roles=[Role.ADMIN],
    )
    return request


@pytest.mark.parametrize("etag", [None, '"0"', "3", '""', '"abc"', '"3', '3"'])
def test_get_returns_json_and_etag(service: Mock, etag: str | None) -> None:
    """Ohne passende Version werden JSON-Daten samt ETag geliefert."""
    request = _request(etag)
    response = get_by_id(1, request, service)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["etag"] == '"3"'
    body = json.loads(bytes(response.body))
    assert body["id"] == 1
    assert body["pruefungsleistungen"][0]["note"] == "1.3"
    assert "version" not in body
    assert service.find_by_id.call_args.kwargs == {
        "student_id": 1,
        "user": request.state.current_user,
    }
    service.find_by_id.assert_called_once()


def test_get_matching_version_returns_empty_response(service: Mock) -> None:
    """Passende Version: 304 ohne JSON-Body und mit aktuellem ETag."""
    response = get_by_id(1, _request('"3"'), service)

    assert response.status_code == HTTPStatus.NOT_MODIFIED
    assert response.body == b""
    assert response.headers["etag"] == '"3"'


def test_get_missing_student_still_raises_not_found(service: Mock) -> None:
    """Ein Header darf den Fehler für eine unbekannte ID nicht verdecken."""
    service.find_by_id.side_effect = NotFoundError(student_id=999999)

    with pytest.raises(NotFoundError):
        get_by_id(999999, _request('"3"'), service)


@pytest.mark.parametrize(
    ("nachname", "email"),
    [
        (None, None),
        ("Muster", None),
        (None, "max@example.org"),
        ("Muster", "max@example.org"),
    ],
)
@pytest.mark.parametrize(("page", "size"), [(0, 5), (1, 2), (3, 0), (0, 100)])
def test_search_passes_filters_to_service(
    service: Mock, nachname: str | None, email: str | None, page: int, size: int
) -> None:
    """Optionale Filter werden unverändert an den Service weitergereicht."""
    service.find.return_value = [service.find_by_id.return_value]
    service.count.return_value = 7

    result = get(
        StudentFindModel(nachname=nachname, email=email, page=page, size=size), service
    )

    service.find.assert_called_once()
    kwargs = service.find.call_args.kwargs
    assert kwargs["nachname"] == nachname
    assert kwargs["email"] == email
    assert kwargs["pageable"].number == page
    assert kwargs["pageable"].size == size
    assert [student.id for student in result.content] == [1]
    assert result.content[0].pruefungsleistungen[0].note == Decimal("1.3")
    service.count.assert_called_once_with(nachname=nachname, email=email)
    assert result.page.model_dump() == {
        "size": size,
        "number": page,
        "total_elements": 7,
        "total_pages": (7 + size - 1) // size if size else 1,
    }
    body = result.model_dump(mode="json")
    assert body["content"][0]["pruefungsleistungen"][0]["note"] == "1.3"
    assert "version" not in body["content"][0]


def test_search_missing_page_raises_not_found(service: Mock) -> None:
    """Eine leere Seite bleibt ein Fehler und wird nicht als leere Seite verpackt."""
    service.find.side_effect = NotFoundError(nachname="xyz")

    with pytest.raises(NotFoundError):
        get(StudentFindModel(nachname="xyz"), service)

    service.count.assert_not_called()


@pytest.fixture
def app(service: Mock, mocker: MockerFixture) -> FastAPI:
    """Produktiven Leserouter mit echter Rollen- und Bearer-Prüfung verwenden."""
    app = FastAPI()
    app.include_router(student_router, prefix="/rest")
    app.exception_handler(AuthorizationError)(authorization_error_handler)
    app.exception_handler(NotFoundError)(not_found_error_handler)
    app.exception_handler(ForbiddenError)(forbidden_error_handler)
    token_service = TokenService.__new__(TokenService)

    def decode(token: str) -> User:
        if token == "invalid":  # ruff: ignore[hardcoded-password-string] -- synthetischer Testtoken
            raise AuthorizationError
        return User(
            username="test",
            email="test@example.org",
            vorname="Test",
            nachname="Test",
            roles=[] if token == "none" else [Role[token.upper()]],  # ruff: ignore[hardcoded-password-string]
        )

    mocker.patch.object(token_service, "get_user_from_token", side_effect=decode)
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_service] = lambda: service
    service.find.return_value = [service.find_by_id.return_value]
    service.count.return_value = 1
    return app


def _get(app: FastAPI, path: str, headers: dict[str, str]) -> httpx.Response:
    """ASGI-Request ohne Server, Datenbank oder Keycloak senden."""

    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client:
            return await client.get(path, headers=headers)

    return asyncio.run(send())


@pytest.mark.parametrize("path", ["/rest/1", "/rest"])
@pytest.mark.parametrize(
    "authorization", [None, "Basic admin", "Bearer", "Bearer invalid"]
)
def test_read_requires_valid_bearer(
    app: FastAPI, service: Mock, path: str, authorization: str | None
) -> None:
    headers = {} if authorization is None else {"Authorization": authorization}
    response = _get(app, path, headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["content-type"] == "application/problem+json"
    assert service.mock_calls == []


@pytest.mark.parametrize(
    ("path", "role", "expected"),
    [
        ("/rest/1", "admin", HTTPStatus.OK),
        ("/rest/1", "student", HTTPStatus.OK),
        ("/rest/1", "none", HTTPStatus.FORBIDDEN),
        ("/rest", "admin", HTTPStatus.OK),
        ("/rest", "student", HTTPStatus.FORBIDDEN),
        ("/rest", "none", HTTPStatus.FORBIDDEN),
    ],
)
def test_read_roles(
    app: FastAPI, service: Mock, path: str, role: str, expected: HTTPStatus
) -> None:
    response = _get(app, path, {"Authorization": f"Bearer {role}"})
    assert response.status_code == expected
    if expected == HTTPStatus.FORBIDDEN:
        assert service.mock_calls == []
    elif path == "/rest/1":
        assert response.json()["id"] == 1
        assert response.headers["etag"] == '"3"'
        service.find_by_id.assert_called_once()
        kwargs = service.find_by_id.call_args.kwargs
        assert kwargs["student_id"] == 1
        assert kwargs["user"].username == "test"
        assert kwargs["user"].roles == [Role[role.upper()]]
    else:
        assert response.json()["content"][0]["id"] == 1
        assert response.json()["page"]["total_elements"] == 1
        service.find.assert_called_once()
        service.count.assert_called_once()


@pytest.mark.parametrize(
    ("authorization", "expected"),
    [
        ("Bearer student", HTTPStatus.NOT_MODIFIED),
        ("Bearer invalid", HTTPStatus.UNAUTHORIZED),
    ],
)
def test_etag_does_not_bypass_authentication(
    app: FastAPI, service: Mock, authorization: str, expected: HTTPStatus
) -> None:
    response = _get(
        app, "/rest/1", {"Authorization": authorization, "If-None-Match": '"3"'}
    )
    assert response.status_code == expected
    if expected == HTTPStatus.NOT_MODIFIED:
        assert response.content == b""
        assert response.headers["etag"] == '"3"'
    else:
        assert service.mock_calls == []


@pytest.mark.parametrize("path", ["/rest/999999", "/rest?nachname=xyz"])
def test_authorized_not_found(app: FastAPI, service: Mock, path: str) -> None:
    service.find_by_id.side_effect = NotFoundError(student_id=999999)
    service.find.side_effect = NotFoundError(nachname="xyz")
    response = _get(app, path, {"Authorization": "Bearer admin"})
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/problem+json"


@pytest.mark.parametrize("etag", [None, '"3"'])
def test_forbidden_datensatz_auch_mit_etag(
    app: FastAPI,
    service: Mock,
    etag: str | None,
) -> None:
    service.find_by_id.side_effect = ForbiddenError
    headers = {"Authorization": "Bearer student"}
    if etag is not None:
        headers["If-None-Match"] = etag

    response = _get(app, "/rest/1", headers)

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "title": "Forbidden",
        "status_code": 403,
        "detail": None,
    }
    assert "etag" not in response.headers
