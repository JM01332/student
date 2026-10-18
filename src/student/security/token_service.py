"""Schnittstelle für die Token-Ausstellung durch Keycloak."""

lazy from collections.abc import Mapping

from keycloak import KeycloakAuthenticationError, KeycloakOpenID, KeycloakOperationError

from student.config import keycloak_config
from student.security.exceptions import LoginError

__all__ = ["TokenService"]


class TokenService:
    """Access und Refresh Token für Benutzer bei Keycloak anfordern."""

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
