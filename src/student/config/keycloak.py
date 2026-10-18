"""Konfiguration für den Zugriff auf Keycloak."""

from dataclasses import dataclass, field
from os import getenv
from pathlib import Path
from typing import Final

from dotenv import dotenv_values

from student.config.config import app_config, resources_path

__all__ = ["KeycloakConfig", "keycloak_config"]


@dataclass(frozen=True, eq=False, slots=True)
class KeycloakConfig:
    """Verbindungsdaten für den OIDC-Client der Anwendung."""

    server_url: str
    realm_name: str
    client_id: str
    client_secret_key: str = field(repr=False)
    verify: str


_keycloak_toml: Final = app_config.get("keycloak", {})
_schema: Final[str] = _keycloak_toml.get("schema", "https")
_host: Final[str] = _keycloak_toml.get("host", "localhost")
_port: Final[int] = _keycloak_toml.get("port", 8843)
_certificate: Final[str] = _keycloak_toml.get("certificate", "certificate.crt")

keycloak_config: Final = KeycloakConfig(
    server_url=f"{_schema}://{_host}:{_port}/",
    realm_name=_keycloak_toml.get("realm", "student"),
    client_id=_keycloak_toml.get("client-id", "student-client"),
    client_secret_key=getenv(
        "CLIENT_SECRET", dotenv_values(Path(".env")).get("CLIENT_SECRET") or ""
    ),
    verify=str(resources_path / "keycloak" / _certificate),
)
"""OIDC-Konfiguration; ein fehlendes Secret bleibt bis zur Anbindung leer."""
