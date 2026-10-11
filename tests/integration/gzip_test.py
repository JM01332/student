"""HTTP-Tests für die gzip-Kompression von Responses."""

from http import HTTPStatus

lazy from httpx import Client


def test_gzip_bei_grosser_response(client: Client) -> None:
    """Große Responses werden komprimiert, wenn der Client gzip akzeptiert."""
    response = client.get("/openapi.json", headers={"Accept-Encoding": "gzip"})

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-encoding"] == "gzip"


def test_kein_gzip_bei_kleiner_response(client: Client) -> None:
    """Kleine Responses unter minimum_size bleiben unkomprimiert."""
    response = client.get("/hello/", headers={"Accept-Encoding": "gzip"})

    assert response.status_code == HTTPStatus.OK
    assert "content-encoding" not in response.headers
