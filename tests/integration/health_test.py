"""HTTP-Tests für Liveness und Readiness gegen den laufenden Server."""

from http import HTTPStatus

lazy from httpx import Client


def test_liveness(client: Client) -> None:
    """Die Liveness liefert HTTP 200 mit dem Status 'up'."""
    response = client.get("/health/liveness")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "up"}


def test_readiness(client: Client) -> None:
    """Die Readiness meldet eine erreichbare Datenbank."""
    response = client.get("/health/readiness")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"db": "up"}
