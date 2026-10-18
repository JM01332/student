"""Gemeinsame Fixtures für die Integrationstests gegen den laufenden Server."""

import os
import ssl
from http import HTTPStatus
from pathlib import Path
from typing import Final
lazy from collections.abc import Iterator

import pytest
from httpx import Client, ConnectError, TimeoutException

BASE_URL: Final = "https://127.0.0.1:8000"
"""URL des laufenden Servers, gestartet mit `uv run python -m student`."""

TIMEOUT: Final = 5.0
"""Timeout in Sekunden für jeden Request."""

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


@pytest.fixture(scope="session")
def client() -> Iterator[Client]:
    """HTTP-Client für alle Integrationstests, der das Server-Zertifikat prüft.

    Bricht den Testlauf mit einem Hinweis ab, falls der Server nicht läuft oder die
    Datenbank nicht erreichbar ist.
    """
    ssl_context: Final = ssl.create_default_context(cafile=_CERTIFICATE)
    with Client(base_url=BASE_URL, verify=ssl_context, timeout=TIMEOUT) as client:
        try:
            readiness = client.get("/health/readiness").json()
        except ConnectError:
            pytest.exit(
                f"Server unter {BASE_URL} nicht erreichbar: zuerst"
                " `uv run python -m student` starten (und PostgreSQL), dann die"
                " Integrationstests ausführen.",
                returncode=1,
            )
        except TimeoutException:
            readiness = {"db": "timeout"}
        if readiness != {"db": "up"}:
            pytest.exit(
                "Der Server läuft, aber die Datenbank ist nicht erreichbar: PostgreSQL"
                " mit `docker compose up` in extras/compose/postgres starten.",
                returncode=1,
            )
        token = os.environ.get("STUDENT_TEST_TOKEN")
        if not token:
            pytest.exit(
                "STUDENT_TEST_TOKEN mit einem aktuellen Admin-Access-Token setzen.",
                returncode=1,
            )
        client.headers["Authorization"] = f"Bearer {token}"
        # Vor dem automatischen DB-Neuladen Authentifizierung und Adminrolle prüfen.
        probe = client.get("/rest", params={"size": 1})
        if probe.status_code not in {HTTPStatus.OK, HTTPStatus.NOT_FOUND}:
            pytest.exit(
                "Admin-Token nicht verwendbar: GET /rest ergibt "
                f"HTTP {probe.status_code}. Keycloak und Token prüfen.",
                returncode=1,
            )
        yield client


@pytest.fixture(scope="session", autouse=True)
def db_neu_laden(client: Client) -> None:
    """DB vor den Integrationstests einmal mit den Testdaten neu laden.

    `autouse=True`: Die Fixture läuft automatisch, ohne dass ein Test sie anfordert.
    So beginnt jeder Testlauf mit denselben Daten, auch wenn ein vorheriger Lauf
    z.B. per POST neue Studierende angelegt hat.
    """
    response = client.request("QUERY", "/dev/db_populate")
    assert response.status_code == HTTPStatus.OK, (
        "DB konnte nicht neu geladen werden: Ist `[dev] db-populate = true` gesetzt?"
    )
