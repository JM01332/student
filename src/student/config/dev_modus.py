"""Konfiguration für den Entwicklungsmodus."""

from typing import Final

from student.config.config import app_config

__all__ = ["dev_db_populate", "dev_keycloak_populate"]

_dev_toml: Final = app_config.get("dev", {})

dev_db_populate: Final[bool] = bool(_dev_toml.get("db-populate", False))
"""Flag, ob die DB beim Serverstart neu geladen werden soll."""

dev_keycloak_populate: Final[bool] = bool(_dev_toml.get("keycloak-populate", False))
"""Flag, ob die Keycloak-Benutzer beim Serverstart neu geladen werden sollen."""
