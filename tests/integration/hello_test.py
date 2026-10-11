"""HTTP-Test für den ersten FastAPI-Endpunkt gegen den laufenden Server."""

from http import HTTPStatus

lazy from httpx import Client


def test_hello(client: Client) -> None:
    """Der Hello-Endpunkt liefert HTTP 200 und den erwarteten JSON-Body."""
    response = client.get("/hello/")

    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"Hello": "World"}
