"""HTTP-Tests für das Anlegen von Studierenden gegen den laufenden Server."""

from http import HTTPStatus
from random import randint
from typing import Any
from uuid import uuid4

lazy from httpx import Client


def _neuer_student() -> dict[str, Any]:
    """Neuer Studierender mit zufälliger Email und Matrikelnummer.

    Zufällige Werte, damit die Tests mehrfach hintereinander laufen können, ohne an
    bereits angelegten Daten zu scheitern (die DB wird nur beim Serverstart neu
    geladen).
    """
    return {
        "matrikelnummer": str(randint(500000, 999999)),  # ruff: ignore[suspicious-non-cryptographic-random-usage]
        "nachname": "Test",
        "vorname": "Theo",
        "email": f"theo.{uuid4().hex[:8]}@h-ka.de",
        "username": "theo",
        "adresse": {"plz": "76133", "ort": "Karlsruhe"},
        "pruefungsleistungen": [
            {"modul": "Softwareengineering", "note": 1.3, "semester": "WS 2026/27"},
        ],
    }


def test_post(client: Client) -> None:
    """Ein neuer Studierender wird mit 201 und Location-Header angelegt."""
    neu = _neuer_student()

    response = client.post("/rest", json=neu)

    assert response.status_code == HTTPStatus.CREATED
    assert response.content == b""
    location = response.headers["location"]
    assert "/rest/" in location

    # Der neue Datensatz lässt sich über die Location wieder lesen
    gelesen = client.get(location)
    assert gelesen.status_code == HTTPStatus.OK
    assert gelesen.json()["email"] == neu["email"]
    assert gelesen.json()["adresse"]["ort"] == "Karlsruhe"
    assert gelesen.json()["pruefungsleistungen"][0]["note"] == "1.3"


def test_post_ungueltige_daten(client: Client) -> None:
    """Ungültige Daten werden von pydantic mit 422 abgewiesen."""
    neu = _neuer_student() | {"matrikelnummer": "12", "email": "keine-email"}

    response = client.post("/rest", json=neu)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    felder = {fehler["loc"][-1] for fehler in response.json()["detail"]}
    assert felder == {"matrikelnummer", "email"}


def test_post_email_existiert(client: Client) -> None:
    """Eine bereits vorhandene Email liefert 422 mit ProblemDetails."""
    neu = _neuer_student() | {"email": "max.mustermann@h-ka.de"}

    response = client.post("/rest", json=neu)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.headers["content-type"] == "application/problem+json"
    assert "max.mustermann@h-ka.de" in response.json()["detail"]


def test_post_matrikelnummer_existiert(client: Client) -> None:
    """Eine bereits vorhandene Matrikelnummer liefert 422 mit ProblemDetails."""
    neu = _neuer_student() | {"matrikelnummer": "123456"}

    response = client.post("/rest", json=neu)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.headers["content-type"] == "application/problem+json"
    assert "123456" in response.json()["detail"]
