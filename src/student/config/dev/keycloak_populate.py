"""Neuladen der Keycloak-Benutzer im Modus DEV."""

from csv import DictReader
from pathlib import Path
from typing import Final

from keycloak import KeycloakConnectionError
from loguru import logger

from student.config.dev_modus import dev_keycloak_populate
from student.config.keycloak import csv_config
from student.security import Role, User
from student.security.dependencies import get_user_service
lazy from student.security import UserService

__all__ = [
    "KeycloakPopulateService",
    "get_keycloak_populate_service",
    "keycloak_populate",
]

_PASSWORD: Final = "p"  # ruff: ignore[hardcoded-password-string]  # NOSONAR
"""Lokales Entwicklungspasswort aller Testbenutzer wie im Beispielprojekt."""


class KeycloakPopulateService:
    """Benutzer in Keycloak passend zu den Testdaten der DB neu anlegen."""

    def __init__(self, user_service: UserService) -> None:
        """Konstruktor mit abhängigem UserService."""
        self.user_service: Final = user_service

    def populate(self) -> None:
        """Alle Benutzer außer admin löschen und aus der CSV-Datei neu anlegen."""
        logger.warning(">>> Keycloak wird neu geladen <<<")
        try:
            self.user_service.remove_all_users()
            self._create_users()
        except KeycloakConnectionError:
            logger.error(">>> Keine Keycloak-Verbindung! Ist Keycloak gestartet? <<<")
            return
        logger.warning(">>> Keycloak wurde neu geladen <<<")

    def _create_users(self) -> None:
        csv_path: Final = Path(csv_config)
        if not csv_path.is_file():
            logger.error("CSV-Datei {} existiert nicht", csv_path.resolve())
            return

        with csv_path.open(encoding="utf-8") as csv_file:
            # DictReader: Spalten über die Kopfzeile ansprechen statt über Indizes
            for row in DictReader(csv_file, delimiter=";"):
                username = row["username"]
                if username == "admin":
                    continue
                user = User(
                    username=username,
                    email=row["email"],
                    nachname=row["nachname"],
                    vorname=row["vorname"],
                    roles=[Role.STUDENT],
                    password=_PASSWORD,
                )
                self.user_service.create_user(user)
                logger.debug("username={}", username)


def get_keycloak_populate_service() -> KeycloakPopulateService:
    """Factory-Funktion für KeycloakPopulateService."""
    return KeycloakPopulateService(get_user_service())


def keycloak_populate() -> None:
    """Keycloak-Benutzer neu laden, falls im Dev-Modus."""
    if dev_keycloak_populate:
        get_keycloak_populate_service().populate()
