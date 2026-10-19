"""Konfiguration für den Zugriff auf Keycloak."""

from dataclasses import dataclass, field
from os import getenv
from pathlib import Path
from typing import Final

from dotenv import dotenv_values

from student.config.config import app_config, resources_path

__all__ = [
    "KeycloakAdminConfig",
    "KeycloakConfig",
    "csv_config",
    "keycloak_admin_config",
    "keycloak_config",
]


@dataclass(frozen=True, eq=False, slots=True)
class KeycloakConfig:
    """Verbindungsdaten für den OIDC-Client der Anwendung."""

    server_url: str
    realm_name: str
    client_id: str
    client_secret_key: str = field(repr=False)
    verify: str


@dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class KeycloakAdminConfig(KeycloakConfig):
    """Zusätzliche Zugangsdaten für die Admin-REST-API von Keycloak.

    Wie im Beispielprojekt meldet sich die Anwendung dafür als Benutzer `admin` im
    eigenen Realm an; dieser braucht die Client-Rollen von `realm-management`.
    """

    username: str
    password: str = field(repr=False)


_keycloak_toml: Final = app_config.get("keycloak", {})
_schema: Final[str] = _keycloak_toml.get("schema", "https")
_host: Final[str] = _keycloak_toml.get("host", "localhost")
_port: Final[int] = _keycloak_toml.get("port", 8843)
_certificate: Final[str] = _keycloak_toml.get("certificate", "certificate.crt")
_server_url: Final = f"{_schema}://{_host}:{_port}/"
_realm: Final[str] = _keycloak_toml.get("realm", "student")
_client_id: Final[str] = _keycloak_toml.get("client-id", "student-client")
_client_secret: Final = getenv(
    "CLIENT_SECRET", dotenv_values(Path(".env")).get("CLIENT_SECRET") or ""
)
_verify: Final = str(resources_path / "keycloak" / _certificate)

keycloak_config: Final = KeycloakConfig(
    server_url=_server_url,
    realm_name=_realm,
    client_id=_client_id,
    client_secret_key=_client_secret,
    verify=_verify,
)
"""OIDC-Konfiguration; ein fehlendes Secret bleibt bis zur Anbindung leer."""

keycloak_admin_config: Final = KeycloakAdminConfig(
    server_url=_server_url,
    realm_name=_realm,
    client_id=_client_id,
    client_secret_key=_client_secret,
    verify=_verify,
    username=_keycloak_toml.get("admin", "admin"),
    password=_keycloak_toml.get("admin-password", ""),
)
"""Zugang zur Admin-REST-API, z.B. zum Anlegen von Benutzern."""

csv_config: Final[str] = _keycloak_toml.get(
    "csv", "extras/compose/postgres/init/student/csv/student.csv"
)
"""CSV-Datei mit den Testdaten, aus der Keycloak im Dev-Modus neu geladen wird.

Ein relativer Pfad gilt ab dem Arbeitsverzeichnis (Projektverzeichnis).
"""
