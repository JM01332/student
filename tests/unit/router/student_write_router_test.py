"""Unit-Tests für PUT mit If-Match ohne Datenbank."""

import json
from http import HTTPStatus
lazy from unittest.mock import Mock

import pytest
from fastapi import Request
lazy from pytest_mock import MockerFixture

from student.router.student_update_model import StudentUpdateModel
from student.router.student_write_router import put
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
