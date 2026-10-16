"""HTTP-Tests für das Ändern von Studierenden gegen den laufenden Server.

Die DB wird nur einmal pro Testlauf neu geladen (Fixture `db_neu_laden`). Die Tests
lesen deshalb vor dem PUT den aktuellen ETag per GET, wie es auch ein echter Client
macht, und hängen so nicht von der Reihenfolge ab.
"""

from http import HTTPStatus
from typing import Any, Final
from uuid import uuid4

import pytest
lazy from httpx import Client

STUDENT_ID: Final = 20
"""Vorhandener Studierender (Erika Musterfrau)."""

GEAENDERT: Final[dict[str, Any]] = {
    "matrikelnummer": "654322",
    "nachname": "Musterfrau-Neu",
    "vorname": "Erika",
    "email": "erika.neu@h-ka.de",
}


def _etag(client: Client, student_id: int = STUDENT_ID) -> str:
    """Aktuellen ETag eines Studierenden per GET lesen, z.B. '"0"'."""
    return client.get(f"/rest/{student_id}").headers["etag"]


def test_put(client: Client) -> None:
    """Passendes If-Match: 204 mit neuem ETag; GET liefert die neuen Daten."""
    etag = _etag(client)
    neue_version = int(etag[1:-1]) + 1

    response = client.put(
        f"/rest/{STUDENT_ID}", json=GEAENDERT, headers={"If-Match": etag}
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response.content == b""
    assert response.headers["etag"] == f'"{neue_version}"'

    gelesen = client.get(f"/rest/{STUDENT_ID}")
    assert gelesen.status_code == HTTPStatus.OK
    assert gelesen.headers["etag"] == f'"{neue_version}"'
    assert gelesen.json()["nachname"] == "Musterfrau-Neu"
    assert gelesen.json()["email"] == "erika.neu@h-ka.de"
    # Adresse und Prüfungsleistungen bleiben beim PUT unverändert
    assert gelesen.json()["adresse"] is not None


def test_put_ohne_if_match(client: Client) -> None:
    """Ohne If-Match: 428 mit ProblemDetails."""
    response = client.put(f"/rest/{STUDENT_ID}", json=GEAENDERT)

    assert response.status_code == HTTPStatus.PRECONDITION_REQUIRED
    assert response.headers["content-type"] == "application/problem+json"


@pytest.mark.parametrize("if_match", ["0", '"abc"'])
def test_put_if_match_ungueltig(client: Client, if_match: str) -> None:
    """Ungültiges If-Match: 412 mit ProblemDetails."""
    response = client.put(
        f"/rest/{STUDENT_ID}", json=GEAENDERT, headers={"If-Match": if_match}
    )

    assert response.status_code == HTTPStatus.PRECONDITION_FAILED
    assert response.headers["content-type"] == "application/problem+json"


def test_put_version_veraltet(client: Client) -> None:
    """Zweites PUT mit demselben (jetzt veralteten) ETag: 412."""
    etag = _etag(client)
    # Neue Email, damit sich die Daten wirklich ändern: Bei identischen Daten
    # schickt SQLAlchemy kein UPDATE und die Version in der DB bleibt gleich
    daten = GEAENDERT | {"email": f"erika.{uuid4().hex[:8]}@h-ka.de"}
    erstes = client.put(f"/rest/{STUDENT_ID}", json=daten, headers={"If-Match": etag})
    assert erstes.status_code == HTTPStatus.NO_CONTENT

    zweites = client.put(
        f"/rest/{STUDENT_ID}", json=GEAENDERT, headers={"If-Match": etag}
    )

    assert zweites.status_code == HTTPStatus.PRECONDITION_FAILED
    assert zweites.headers["content-type"] == "application/problem+json"
    assert f"Veraltete Version: {etag[1:-1]}" in zweites.json()["detail"]


@pytest.mark.parametrize("student_id", [0, 999999])
def test_put_nicht_vorhanden(client: Client, student_id: int) -> None:
    """Nicht vorhandene ID: 404."""
    response = client.put(
        f"/rest/{student_id}", json=GEAENDERT, headers={"If-Match": '"0"'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_put_email_existiert(client: Client) -> None:
    """Email eines anderen Studierenden: 422 mit ProblemDetails."""
    daten = GEAENDERT | {"email": "max.mustermann@h-ka.de"}

    response = client.put(
        f"/rest/{STUDENT_ID}", json=daten, headers={"If-Match": _etag(client)}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert "max.mustermann@h-ka.de" in response.json()["detail"]


def test_put_matrikelnummer_existiert(client: Client) -> None:
    """Matrikelnummer eines anderen Studierenden: 422 mit ProblemDetails."""
    daten = GEAENDERT | {"matrikelnummer": "123456"}

    response = client.put(
        f"/rest/{STUDENT_ID}", json=daten, headers={"If-Match": _etag(client)}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert "123456" in response.json()["detail"]


def test_put_ungueltige_daten(client: Client) -> None:
    """Ungültige Daten werden von pydantic mit 422 abgewiesen."""
    daten = GEAENDERT | {"matrikelnummer": "12", "email": "keine-email"}

    response = client.put(
        f"/rest/{STUDENT_ID}", json=daten, headers={"If-Match": _etag(client)}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    felder = {fehler["loc"][-1] for fehler in response.json()["detail"]}
    assert felder == {"matrikelnummer", "email"}
