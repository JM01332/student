"""HTTP-Tests für die gzip-Kompression von Responses."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from student.fastapi_app import app


def test_gzip_bei_grosser_response() -> None:
    """Große Responses werden komprimiert, wenn der Client gzip akzeptiert."""
    with TestClient(app) as client:
        response = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-encoding"] == "gzip"


def test_kein_gzip_bei_kleiner_response() -> None:
    """Kleine Responses unter minimum_size bleiben unkomprimiert."""
    with TestClient(app) as client:
        response = client.get("/hello/", headers={"Accept-Encoding": "gzip"})

    assert response.status_code == HTTPStatus.OK
    assert "content-encoding" not in response.headers
