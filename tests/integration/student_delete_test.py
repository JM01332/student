"""HTTP-Tests für das Löschen von Studierenden gegen den laufenden Server.

Die DB wird nur einmal pro Testlauf neu geladen. Damit die anderen Tests ihre
Testdaten behalten, legt der Test seinen Studierenden selbst per POST an.
"""

from http import HTTPStatus
from random import randint
from uuid import uuid4

import pytest
lazy from httpx import Client


def _neuer_student_location(client: Client) -> str:
    """Neuen Studierenden per POST anlegen und die Location-URL liefern."""
    neu = {
        "matrikelnummer": str(randint(500000, 999999)),  # ruff: ignore[suspicious-non-cryptographic-random-usage]
        "nachname": "Loeschen",
        "vorname": "Lea",
        "email": f"lea.{uuid4().hex[:8]}@h-ka.de",
        "username": "lea",
        "adresse": {"plz": "76133", "ort": "Karlsruhe"},
        "pruefungsleistungen": [
            {"modul": "Softwareengineering", "note": 1.3, "semester": "WS 2026/27"},
        ],
    }
    response = client.post("/rest", json=neu)
    assert response.status_code == HTTPStatus.CREATED
    return response.headers["location"]


def test_delete(client: Client) -> None:
    """Löschen liefert 204; danach ist der Studierende nicht mehr lesbar."""
    location = _neuer_student_location(client)

    response = client.delete(location)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert client.get(location).status_code == HTTPStatus.NOT_FOUND


def test_delete_zweimal(client: Client) -> None:
    """Idempotent: Auch das zweite Löschen derselben ID liefert 204."""
    location = _neuer_student_location(client)
    assert client.delete(location).status_code == HTTPStatus.NO_CONTENT

    response = client.delete(location)

    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.parametrize("student_id", [0, 999999])
def test_delete_nicht_vorhanden(client: Client, student_id: int) -> None:
    """Eine nicht vorhandene ID ist kein Fehler: 204."""
    response = client.delete(f"/rest/{student_id}")

    assert response.status_code == HTTPStatus.NO_CONTENT
