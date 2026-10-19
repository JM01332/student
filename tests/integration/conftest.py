"""Gemeinsame Fixtures für die Integrationstests gegen den laufenden Server."""

import ssl
from http import HTTPStatus
from pathlib import Path
from typing import Final
lazy from collections.abc import Callable, Iterator

import pytest
from httpx import Client, ConnectError, TimeoutException

BASE_URL: Final = "https://127.0.0.1:8000"
"""URL des laufenden Servers, gestartet mit `uv run python -m student`."""

TIMEOUT: Final = 5.0
"""Timeout in Sekunden für jeden Request."""

TOKEN_PATH: Final = "/auth/token"  # ruff: ignore[hardcoded-password-string]
"""Login an der REST-Schnittstelle wie im Beispielprojekt."""

USERNAME_ADMIN: Final = "admin"
"""Benutzer im Keycloak-Realm `student` mit der Rolle admin."""

PASSWORD_ADMIN: Final = "p"  # ruff: ignore[hardcoded-password-string]
"""Lokales Entwicklungspasswort aus der Keycloak-Anleitung."""

_CERTIFICATE: Final = (
    Path(__file__).parents[2]
    / "src"
    / "student"
    / "config"
    / "resources"
    / "tls"
    / "certificate.crt"
)
"""Selbstsigniertes Zertifikat des Servers, dem die Tests vertrauen."""


def _neuer_client() -> Client:
    """HTTP-Client ohne Token, der dem Server-Zertifikat vertraut."""
    ssl_context: Final = ssl.create_default_context(cafile=_CERTIFICATE)
    return Client(base_url=BASE_URL, verify=ssl_context, timeout=TIMEOUT)


@pytest.fixture(scope="session")
def client_ohne_token() -> Iterator[Client]:
    """HTTP-Client ohne Authorization-Header, z.B. für Login und 401-Tests.

    Bricht den Testlauf mit einem Hinweis ab, falls der Server nicht läuft oder die
    Datenbank nicht erreichbar ist.
    """
    with _neuer_client() as client:
        try:
            readiness = client.get("/health/readiness").json()
        except ConnectError:
            pytest.exit(
                f"Server unter {BASE_URL} nicht erreichbar: zuerst"
                " `uv run python -m student` starten (und das Backend), dann die"
                " Integrationstests ausführen.",
                returncode=1,
            )
        except TimeoutException:
            readiness = {"db": "timeout"}
        if readiness != {"db": "up"}:
            pytest.exit(
                "Der Server läuft, aber die Datenbank ist nicht erreichbar: PostgreSQL"
                " und Keycloak mit `docker compose up -d` in extras/compose/backend"
                " starten.",
                returncode=1,
            )
        yield client


@pytest.fixture(scope="session")
def login(client_ohne_token: Client) -> Callable[[str, str], str]:
    """Funktion zum Einloggen, die ein Access Token von Keycloak liefert.

    Wie `login()` im Beispielprojekt: `QUERY /auth/token` mit Benutzername und
    Passwort an den eigenen Server. Als Fixture, damit Tests sich auch mit anderen
    Benutzern anmelden können, z.B. `login("student", "p")`.
    """

    def _login(username: str, password: str) -> str:
        response: Final = client_ohne_token.request(
            "QUERY",
            TOKEN_PATH,
            json={"username": username, "password": password},
        )
        if response.status_code != HTTPStatus.OK:
            pytest.exit(
                f"Login als {username} mit HTTP {response.status_code}: Läuft"
                " Keycloak, und steht CLIENT_SECRET in der .env?",
                returncode=1,
            )
        return response.json()["token"]

    return _login


@pytest.fixture(scope="session")
def client(login: Callable[[str, str], str]) -> Iterator[Client]:
    """HTTP-Client mit dem Token des Administrators für alle REST-Tests.

    Das Token wird einmal pro Testlauf geholt; es gilt 30 Minuten und damit
    deutlich länger als ein Testlauf.
    """
    token: Final = login(USERNAME_ADMIN, PASSWORD_ADMIN)
    with _neuer_client() as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


@pytest.fixture(scope="session", autouse=True)
def testdaten_neu_laden(client: Client) -> None:
    """DB und Keycloak-Benutzer vor den Integrationstests einmal neu laden.

    `autouse=True`: Die Fixture läuft automatisch, ohne dass ein Test sie anfordert.
    So beginnt jeder Testlauf mit denselben Daten, auch wenn ein vorheriger Lauf
    z.B. per POST neue Studierende (und damit Keycloak-Benutzer) angelegt hat.
    """
    response = client.request("QUERY", "/dev/db_populate")
    assert response.status_code == HTTPStatus.OK, (
        "DB konnte nicht neu geladen werden: Ist `[dev] db-populate = true` gesetzt?"
    )
    response = client.request("QUERY", "/dev/keycloak_populate")
    assert response.status_code == HTTPStatus.OK, (
        "Keycloak konnte nicht neu geladen werden: Ist `[dev] keycloak-populate ="
        " true` gesetzt?"
    )
