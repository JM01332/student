"""HTTP-Tests für Login und Zugriffsschutz gegen Server und echten Keycloak.

Angelehnt an `tests/integration/security/login_test.py` und
`tests/integration/rest/get_by_id_test.py` im Beispielprojekt.
"""

from http import HTTPStatus
from typing import Final
lazy from collections.abc import Callable

import pytest
lazy from httpx import Client

TOKEN_PATH: Final = "/auth/token"  # ruff: ignore[hardcoded-password-string]
USERNAME_ADMIN: Final = "admin"
USERNAME_STUDENT: Final = "erika"
"""Studierende aus den Testdaten mit der Rolle student (ohne Admin-Rechte).

Wird beim Neuladen von Keycloak aus der CSV-Datei angelegt.
"""

PASSWORD: Final = "p"  # ruff: ignore[hardcoded-password-string]
"""Lokales Entwicklungspasswort beider Testbenutzer."""

TOKEN_LAUFZEIT: Final = 1800
"""Laufzeit des Access Tokens in Sekunden (30 Minuten laut Realm-Einstellung)."""

JWT_TEILE: Final = 3
"""Ein JWT besteht aus Header, Payload und Signatur, getrennt durch Punkte."""


def test_login_admin(client_ohne_token: Client) -> None:
    """Richtige Zugangsdaten liefern ein Token mit Laufzeit und Rolle admin."""
    response = client_ohne_token.request(
        "QUERY",
        TOKEN_PATH,
        json={"username": USERNAME_ADMIN, "password": PASSWORD},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert len(body["token"].split(".")) == JWT_TEILE
    assert body["expires_in"] == TOKEN_LAUFZEIT
    assert "admin" in [rolle.lower() for rolle in body["rollen"]]


@pytest.mark.parametrize(
    "login_data",
    [
        {"username": USERNAME_ADMIN, "password": "FALSCHES_PASSWORT"},
        {"username": "gibt-es-nicht", "password": PASSWORD},
        {},
    ],
)
def test_login_ungueltig(client_ohne_token: Client, login_data: dict[str, str]) -> None:
    """Falsches Passwort, unbekannter Benutzer oder leerer Body: 401."""
    response = client_ohne_token.request("QUERY", TOKEN_PATH, json=login_data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize("student_id", [1, 20])
def test_get_by_id_ohne_token(client_ohne_token: Client, student_id: int) -> None:
    """Ohne Authorization-Header: 401 mit ProblemDetails."""
    response = client_ohne_token.get(f"/rest/{student_id}")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["content-type"] == "application/problem+json"


@pytest.mark.parametrize("student_id", [1, 20])
def test_get_by_id_ungueltiger_token(
    client_ohne_token: Client,
    login: Callable[[str, str], str],
    student_id: int,
) -> None:
    """Verfälschtes Token (wie im Beispielprojekt mit angehängtem XXX): 401."""
    token = login(USERNAME_ADMIN, PASSWORD)

    response = client_ohne_token.get(
        f"/rest/{student_id}", headers={"Authorization": f"Bearer {token}XXX"}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_suche_als_student(
    client_ohne_token: Client, login: Callable[[str, str], str]
) -> None:
    """Gültiges Token, aber ohne Rolle admin: Die Suche liefert 403."""
    token = login(USERNAME_STUDENT, PASSWORD)

    response = client_ohne_token.get(
        "/rest", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
