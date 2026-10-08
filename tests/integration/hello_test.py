"""HTTP-Test für den ersten FastAPI-Endpunkt ohne externe Dienste."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from student.fastapi_app import app


def test_hello() -> None:
    """Der Hello-Endpunkt liefert HTTP 200 und den erwarteten JSON-Body."""
    with TestClient(app) as client:
        response = client.get("/hello/")

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"Hello": "World"}
