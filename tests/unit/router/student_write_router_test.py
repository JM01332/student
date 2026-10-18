"""Unit-Tests für POST-Rollenschutz, PUT und DELETE ohne Datenbank."""

import asyncio
import json
from http import HTTPStatus
lazy from unittest.mock import Mock

import httpx
import pytest
from fastapi import FastAPI, Request
lazy from pytest_mock import MockerFixture

from student.fastapi_app import authorization_error_handler
from student.router.dependencies import get_write_service
from student.router.student_update_model import StudentUpdateModel
from student.router.student_write_router import delete_by_id, put, student_write_router
from student.security import AuthorizationError, Role, TokenService, User
from student.security.dependencies import get_token_service
from student.service import StudentDTO, StudentWriteService, VersionOutdatedError

STUDENT_ID = 1000
VERSION = 3
NEUE_VERSION = VERSION + 1


@pytest.fixture
def service(mocker: MockerFixture) -> Mock:
    """Service-Attrappe, die das DTO mit erhöhter Version zurückliefert."""
    mock = mocker.Mock(spec=StudentWriteService)
    mock.update.return_value = StudentDTO(
        id=STUDENT_ID,
        version=NEUE_VERSION,
        matrikelnummer="123456",
        nachname="Mustermann",
        vorname="Max",
        email="max@example.org",
        username="N/A",
        adresse=None,
        pruefungsleistungen=[],
    )
    return mock


@pytest.fixture
def update_model() -> StudentUpdateModel:
    """Gültige neue Daten."""
    return StudentUpdateModel(
        matrikelnummer="123456",
        nachname="Mustermann",
        vorname="Max",
        email="max@example.org",
    )


def _request(if_match: str | None) -> Request:
    """Request mit optionalem If-Match-Header erzeugen."""
    headers = [] if if_match is None else [(b"if-match", if_match.encode("ascii"))]
    return Request({"type": "http", "headers": headers})


def test_put(service: Mock, update_model: StudentUpdateModel) -> None:
    """Passende Version: 204 ohne Body und mit neuem ETag."""
    response = put(STUDENT_ID, update_model, _request(f'"{VERSION}"'), service)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.body == b""
    assert response.headers["etag"] == f'"{NEUE_VERSION}"'
    service.update.assert_called_once()
    assert service.update.call_args.kwargs["student_id"] == STUDENT_ID
    assert service.update.call_args.kwargs["version"] == VERSION


def test_put_ohne_if_match(service: Mock, update_model: StudentUpdateModel) -> None:
    """Ohne If-Match: 428 als ProblemDetails, der Service wird nicht aufgerufen."""
    response = put(STUDENT_ID, update_model, _request(None), service)

    assert response.status_code == HTTPStatus.PRECONDITION_REQUIRED
    assert response.headers["content-type"] == "application/problem+json"
    body = json.loads(bytes(response.body))
    assert body["status_code"] == HTTPStatus.PRECONDITION_REQUIRED
    service.update.assert_not_called()


@pytest.mark.parametrize("if_match", ["3", '""', '"3', '3"', '"abc"'])
def test_put_if_match_ungueltig(
    service: Mock, update_model: StudentUpdateModel, if_match: str
) -> None:
    """Ungültiges If-Match: 412 als ProblemDetails, ohne Aufruf des Service."""
    response = put(STUDENT_ID, update_model, _request(if_match), service)

    assert response.status_code == HTTPStatus.PRECONDITION_FAILED
    assert response.headers["content-type"] == "application/problem+json"
    service.update.assert_not_called()


def test_put_version_veraltet(service: Mock, update_model: StudentUpdateModel) -> None:
    """Die Exception des Service wird an den Errorhandler (412) weitergereicht."""
    service.update.side_effect = VersionOutdatedError(version=VERSION - 1)

    with pytest.raises(VersionOutdatedError):
        put(STUDENT_ID, update_model, _request(f'"{VERSION - 1}"'), service)


def test_delete(service: Mock) -> None:
    """DELETE: 204 ohne Body; der Service bekommt die ID."""
    response = delete_by_id(STUDENT_ID, service)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.body == b""
    service.delete_by_id.assert_called_once_with(student_id=STUDENT_ID)


@pytest.fixture
def app(service: Mock, mocker: MockerFixture) -> FastAPI:
    """Schreibrouter mit echter Rollen- und Bearer-Prüfung ohne Keycloak."""
    app = FastAPI()
    app.include_router(student_write_router, prefix="/rest")
    app.exception_handler(AuthorizationError)(authorization_error_handler)
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
    app.dependency_overrides[get_write_service] = lambda: service
    service.create.return_value = service.update.return_value
    return app


@pytest.fixture
def payload() -> dict[str, object]:
    """Gültige Daten zum Anlegen eines Studierenden."""
    return {
        "matrikelnummer": "123456",
        "nachname": "Mustermann",
        "vorname": "Max",
        "email": "max@example.org",
        "username": "max",
        "adresse": {"plz": "76133", "ort": "Karlsruhe"},
        "pruefungsleistungen": [],
    }


def _post(
    app: FastAPI, authorization: str | None, payload: dict[str, object]
) -> httpx.Response:
    """ASGI-Request ohne Server, Datenbank oder Keycloak senden."""
    headers = {} if authorization is None else {"Authorization": authorization}

    async def send() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client:
            return await client.post("/rest", headers=headers, json=payload)

    return asyncio.run(send())


@pytest.mark.parametrize(
    "authorization", [None, "Basic admin", "Bearer", "Bearer invalid"]
)
def test_post_requires_valid_bearer(
    app: FastAPI, service: Mock, payload: dict[str, object], authorization: str | None
) -> None:
    response = _post(app, authorization, payload)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["content-type"] == "application/problem+json"
    assert service.mock_calls == []


@pytest.mark.parametrize("role", ["student", "none"])
def test_post_requires_admin(
    app: FastAPI, service: Mock, payload: dict[str, object], role: str
) -> None:
    response = _post(app, f"Bearer {role}", payload)
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert service.mock_calls == []


def test_post_admin(app: FastAPI, service: Mock, payload: dict[str, object]) -> None:
    response = _post(app, "Bearer admin", payload)
    assert response.status_code == HTTPStatus.CREATED
    assert response.content == b""
    assert response.headers["location"] == f"https://test/rest/{STUDENT_ID}"
    service.create.assert_called_once()
    student = service.create.call_args.kwargs["student"]
    assert student.username == payload["username"]
    assert student.email == payload["email"]
    assert student.adresse.ort == "Karlsruhe"


@pytest.mark.parametrize(
    ("authorization", "expected"),
    [
        (None, HTTPStatus.UNAUTHORIZED),
        ("Bearer student", HTTPStatus.FORBIDDEN),
        ("Bearer admin", HTTPStatus.UNPROCESSABLE_CONTENT),
    ],
)
def test_post_invalid_data(
    app: FastAPI, service: Mock, authorization: str | None, expected: HTTPStatus
) -> None:
    """Rollenprüfung vor Modellvalidierung; ADMIN erhält weiterhin 422."""
    response = _post(app, authorization, {})
    assert response.status_code == expected
    assert service.mock_calls == []
