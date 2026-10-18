"""Schnittstelle für die Token-Ausstellung und -Auswertung durch Keycloak."""

from typing import Any
lazy from collections.abc import Mapping

from jwcrypto.common import JWException
from keycloak import KeycloakAuthenticationError, KeycloakOpenID, KeycloakOperationError

from student.config import keycloak_config
from student.security.exceptions import AuthorizationError, LoginError
from student.security.role import Role
from student.security.user import User

__all__ = ["TokenService"]


class TokenService:
    """Tokens anfordern und Benutzerdaten aus Access Tokens ermitteln."""

    def __init__(self) -> None:
        """OIDC-Client mit der vorhandenen Konfiguration initialisieren."""
        self.keycloak = KeycloakOpenID(
            server_url=keycloak_config.server_url,
            realm_name=keycloak_config.realm_name,
            client_id=keycloak_config.client_id,
            client_secret_key=keycloak_config.client_secret_key,
            verify=keycloak_config.verify,
        )

    def token(self, username: str | None, password: str | None) -> Mapping[str, object]:
        """Tokenantwort anfordern; fehlende oder abgelehnte Daten ergeben LoginError.

        Die Antwort enthält Access und Refresh Token sowie Ablaufangaben.
        Passwörter, Tokens und Keycloak-Fehlerantworten werden nicht protokolliert.
        """
        if username is None or password is None:
            raise LoginError(username=username)

        try:
            return self.keycloak.token(username, password)
        except (KeycloakAuthenticationError, KeycloakOperationError) as err:
            raise LoginError(username=username) from err

    def get_user_from_token(self, token: str) -> User:
        """Token prüfen und Benutzer mit Client-Rollen wie im Beispiel ermitteln.

        JWT-Fehler sowie fehlende oder ungültige Claims ergeben AuthorizationError.
        Tokens und decodierte Benutzerdaten werden nicht protokolliert.
        """
        try:
            token_decoded = self.keycloak.decode_token(token=token)
            username: str = token_decoded["preferred_username"]
            email: str = token_decoded["email"]
            nachname: str = token_decoded["family_name"]
            vorname: str = token_decoded["given_name"]
            roles = self._get_roles_from_token(token_decoded)
        except (JWException, KeyError, TypeError, ValueError) as err:
            raise AuthorizationError from err

        return User(
            username=username,
            email=email,
            nachname=nachname,
            vorname=vorname,
            roles=roles,
        )

    def _get_roles_from_token(self, token: Mapping[str, Any]) -> list[Role]:
        """Rollen des konfigurierten Clients auf die Anwendungsrollen abbilden."""
        roles = token["resource_access"][self.keycloak.client_id]["roles"]
        return [Role[role.upper()] for role in roles]
