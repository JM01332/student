"""HTTP-Tests für das Lesen von Studierenden ohne externe Dienste."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from student.fastapi_app import app


def test_get_by_id() -> None:
    """Ein vorhandener Studierender wird mit HTTP 200 und seinen Daten geliefert."""
    with TestClient(app) as client:
        response = client.get("/rest/1")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["nachname"] == "Mustermann"


def test_get_by_id_not_found() -> None:
    """Für eine nicht vorhandene ID wird HTTP 404 geliefert."""
    with TestClient(app) as client:
        response = client.get("/rest/999")

    assert response.status_code == HTTPStatus.NOT_FOUND
