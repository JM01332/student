"""HTTP-Tests für die Security-Header in Responses."""

from http import HTTPStatus

lazy from httpx import Client


def test_security_header(client: Client) -> None:
    """Jede Response enthält die Header für IT-Sicherheit."""
    response = client.get("/hello/")

    assert response.status_code == HTTPStatus.OK
    headers = response.headers
    assert headers["strict-transport-security"] == (
        "max-age=31536000; includeSubDomains"
    )
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "SAMEORIGIN"
    assert headers["content-security-policy"] == (
        "default-src 'self'; object-src 'none'"
    )
    assert headers["x-xss-protection"] == "1; mode=block"


def test_security_header_bei_fehler(client: Client) -> None:
    """Auch Fehler-Responses wie 404 enthalten die Security-Header."""
    response = client.get("/rest/999")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["x-content-type-options"] == "nosniff"
