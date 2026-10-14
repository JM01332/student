"""Unit-Tests für bedingte GET-Requests ohne Datenbank."""

import json
from decimal import Decimal
from http import HTTPStatus
lazy from unittest.mock import Mock

import pytest
from fastapi import Request
lazy from pytest_mock import MockerFixture

from student.router.student_router import get_by_id
from student.service import PruefungsleistungDTO, StudentDTO, StudentService
from student.service.exceptions import NotFoundError


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
    return Request({"type": "http", "headers": headers})


@pytest.mark.parametrize("etag", [None, '"0"', "3", '""', '"abc"', '"3', '3"'])
def test_get_returns_json_and_etag(service: Mock, etag: str | None) -> None:
    """Ohne passende Version werden JSON-Daten samt ETag geliefert."""
    response = get_by_id(1, _request(etag), service)

    assert response.status_code == HTTPStatus.OK
    assert response.headers["etag"] == '"3"'
    body = json.loads(bytes(response.body))
    assert body["id"] == 1
    assert body["pruefungsleistungen"][0]["note"] == "1.3"
    assert "version" not in body
    service.find_by_id.assert_called_once_with(1)


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
