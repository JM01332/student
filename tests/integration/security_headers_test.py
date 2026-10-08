"""HTTP-Tests für die Security-Header in Responses."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from student.fastapi_app import app


def test_security_header() -> None:
    """Jede Response enthält die Header für IT-Sicherheit."""
    with TestClient(app) as client:
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


def test_security_header_bei_fehler() -> None:
    """Auch Fehler-Responses wie 404 enthalten die Security-Header."""
    with TestClient(app) as client:
        response = client.get("/rest/999")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["x-content-type-options"] == "nosniff"
