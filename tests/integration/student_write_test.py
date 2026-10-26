"""HTTP-Tests für das Anlegen von Studierenden gegen den laufenden Server."""

from http import HTTPStatus
from itertools import count
from typing import Any, Final
from uuid import uuid4
lazy from collections.abc import Callable

lazy from httpx import Client

_matrikelnummern: Final = count(900000)
"""Fortlaufende Matrikelnummern ohne Kollision mit den Testdaten.

Die DB wird zu Beginn jedes Testlaufs neu geladen, deshalb reicht ein Zähler; jede
Testdatei hat ihren eigenen Bereich.
"""


def _neuer_student() -> dict[str, Any]:
    """Neuer Studierender mit eindeutiger Email, Matrikelnummer und Benutzername.

    Eindeutige Werte, weil mehrere Tests im selben Testlauf Studierende anlegen.
    """
    return {
        "matrikelnummer": str(next(_matrikelnummern)),
        "nachname": "Test",
        "vorname": "Theo",
        "email": f"theo.{uuid4().hex[:8]}@h-ka.de",
        "username": f"theo{uuid4().hex[:8]}",
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


def test_post_neuer_benutzer_kann_sich_einloggen(
    client: Client, client_ohne_token: Client, login: Callable[[str, str], str]
) -> None:
    """POST legt auch den Keycloak-Benutzer an: Login und Lesen des eigenen Satzes."""
    neu = _neuer_student()
    location = client.post("/rest", json=neu).headers["location"]

    token = login(neu["username"], "p")
    response = client_ohne_token.get(
        location, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["username"] == neu["username"]


def test_post_username_existiert(client: Client) -> None:
    """Einen Benutzernamen, den es in Keycloak gibt, lehnt der Server mit 422 ab."""
    neu = _neuer_student() | {"username": "erika"}

    response = client.post("/rest", json=neu)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.headers["content-type"] == "application/problem+json"
    assert "erika" in response.json()["detail"]
