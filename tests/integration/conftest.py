"""Gemeinsame Fixtures für die Integrationstests gegen den laufenden Server."""

import ssl
from pathlib import Path
from typing import Final
lazy from collections.abc import Iterator

import pytest
from httpx import Client, ConnectError, TimeoutException

BASE_URL: Final = "https://127.0.0.1:8000"
"""URL des laufenden Servers, gestartet mit `uv run student`."""

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
                f"Server unter {BASE_URL} nicht erreichbar: zuerst `uv run student`"
                " starten (und PostgreSQL), dann die Integrationstests ausführen.",
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
        yield client
