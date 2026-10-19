"""Management der Benutzerdaten mit der Admin-REST-API von Keycloak."""

from typing import Any, Final, cast

from keycloak import KeycloakAdmin, KeycloakConnectionError
from loguru import logger

from student.config import keycloak_admin_config
lazy from student.security.user import User

__all__ = ["UserService"]

ROLLE_STUDENT: Final = "student"
"""Client-Rolle in Keycloak, die neue Benutzer erhalten (kleingeschrieben)."""


class UserService:
    """Benutzer in Keycloak suchen, anlegen und löschen."""

    def __init__(self) -> None:
        """Admin-Schnittstelle zu Keycloak initialisieren.

        Wie im Beispielprojekt meldet sich die Anwendung als `admin` im eigenen Realm
        an. Die interne UUID des Clients und die Rolle `student` werden einmal
        ermittelt, weil Keycloak sie beim Zuweisen der Rolle erwartet.
        """
        self.keycloak_admin = KeycloakAdmin(
            server_url=keycloak_admin_config.server_url,
            username=keycloak_admin_config.username,
            password=keycloak_admin_config.password,
            realm_name=keycloak_admin_config.realm_name,
            client_id=keycloak_admin_config.client_id,
            client_secret_key=keycloak_admin_config.client_secret_key,
            verify=keycloak_admin_config.verify,
        )
        try:
            # GET /admin/realms/{realm}/clients?clientId=student-client
            self.client_uuid: str | None = self.keycloak_admin.get_client_id(
                keycloak_admin_config.client_id
            )
            # GET /admin/realms/{realm}/clients/{client-uuid}/roles
            roles = self.keycloak_admin.get_client_roles(
                client_id=cast("str", self.client_uuid)
            )
            self.rolle_student: dict[str, Any] | None = next(
                (role for role in roles if role["name"] == ROLLE_STUDENT), None
            )
        except KeycloakConnectionError:
            logger.error("Keine Verbindung zu Keycloak! Ist Keycloak gestartet?")
            self.client_uuid = None
            self.rolle_student = None
        logger.debug(
            "client_uuid={}, rolle_student={}", self.client_uuid, self.rolle_student
        )

    def username_exists(self, username: str) -> bool:
        """Abfrage, ob es den Benutzernamen in Keycloak bereits gibt.

        :param username: Der zu prüfende Benutzername
        :return: True, falls der Benutzername bereits existiert, False sonst
        :rtype: bool
        :raises KeycloakError: Falls mit Keycloak ein Fehler auftritt
        """
        logger.debug("username={}", username)
        # GET /admin/realms/{realm}/users?username=...&exact=true
        user_id: Final = self.keycloak_admin.get_user_id(username)
        return user_id is not None

    def email_exists(self, email: str) -> bool:
        """Abfrage, ob es die Emailadresse in Keycloak bereits gibt.

        :param email: Die zu prüfende Emailadresse
        :return: True, falls die Emailadresse bereits existiert, False sonst
        :rtype: bool
        :raises KeycloakError: Falls mit Keycloak ein Fehler auftritt
        """
        logger.debug("email={}", email)
        # GET /admin/realms/{realm}/users?email=...
        users: Final = self.keycloak_admin.get_users(query={"email": email})
        return len(users) > 0

    def create_user(self, user: User) -> str:
        """Einen neuen Benutzer mit der Client-Rolle `student` anlegen.

        :param user: Der neue Benutzer mit Passwort
        :return: Die von Keycloak vergebene ID des Benutzers
        :rtype: str
        :raises KeycloakError: Falls mit Keycloak ein Fehler auftritt
        """
        logger.debug("user={}", user)
        # POST /admin/realms/{realm}/users
        user_id: Final = self.keycloak_admin.create_user(
            payload={
                "username": user.username,
                "email": user.email,
                "lastName": user.nachname,
                "firstName": user.vorname,
                "credentials": [{"value": user.password, "type": "password"}],
                "enabled": True,
            },
            exist_ok=False,
        )
        logger.debug("user_id={}", user_id)
        # POST /admin/realms/{realm}/users/{user-id}/role-mappings/clients/{client-uuid}
        self.keycloak_admin.assign_client_role(
            user_id=user_id,
            client_id=cast("str", self.client_uuid),
            roles=[self.rolle_student],
        )
        return user_id

    def remove_all_users(self) -> None:
        """Alle Benutzer außer `admin` aus Keycloak entfernen."""
        # GET /admin/realms/{realm}/users
        for kc_user in self.keycloak_admin.get_users():
            if kc_user.get("username") == keycloak_admin_config.username:
                continue
            # DELETE /admin/realms/{realm}/users/{user-id}
            self.keycloak_admin.delete_user(kc_user["id"])
