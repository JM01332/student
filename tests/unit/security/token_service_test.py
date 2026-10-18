"""Token-Ausstellung ohne Keycloak-Verbindung mit Mocks prüfen."""

lazy from unittest.mock import Mock

import pytest
from keycloak import KeycloakAuthenticationError, KeycloakOperationError
lazy from pytest_mock import MockerFixture

from student.config.keycloak import KeycloakConfig
from student.security import LoginError, TokenService

# Ausschließlich Dummy für den gemockten Client.
TEST_SECRET = "test-secret"  # ruff: ignore[hardcoded-password-string]


@pytest.fixture
def client_factory(mocker: MockerFixture) -> Mock:
    """OIDC-Client und Konfiguration ohne echte Zugangsdaten bereitstellen."""
    mocker.patch(
        "student.security.token_service.keycloak_config",
        KeycloakConfig(
            server_url="https://keycloak.example/",
            realm_name="test-realm",
            client_id="test-client",
            client_secret_key=TEST_SECRET,
            verify="test-certificate.crt",
        ),
    )
    return mocker.patch("student.security.token_service.KeycloakOpenID", autospec=True)


def test_initialization(client_factory: Mock) -> None:
    service = TokenService()
    client_factory.assert_called_once_with(
        server_url="https://keycloak.example/",
        realm_name="test-realm",
        client_id="test-client",
        client_secret_key=TEST_SECRET,
        verify="test-certificate.crt",
    )
    assert service.keycloak is client_factory.return_value
    client_factory.return_value.token.assert_not_called()


def test_token_response(client_factory: Mock) -> None:
    response = {
        "access_token": "test-access",
        "refresh_token": "test-refresh",
        "expires_in": 1800,
        "token_type": "Bearer",
    }
    client_factory.return_value.token.return_value = response
    assert TokenService().token("student", "test-password") is response
    client_factory.return_value.token.assert_called_once_with(
        "student", "test-password"
    )


@pytest.mark.parametrize(
    ("username", "password"),
    [(None, "test-password"), ("student", None), (None, None)],
)
def test_missing_credentials(
    client_factory: Mock, username: str | None, password: str | None
) -> None:
    with pytest.raises(LoginError) as error:
        TokenService().token(username, password)
    assert error.value.username == username
    client_factory.return_value.token.assert_not_called()


@pytest.mark.parametrize(
    "error_type", [KeycloakAuthenticationError, KeycloakOperationError]
)
def test_keycloak_error(client_factory: Mock, error_type: type[Exception]) -> None:
    original = error_type("Rejected")
    client_factory.return_value.token.side_effect = original
    with pytest.raises(
        LoginError, match="Fehlerhafte Benutzerdaten fuer student"
    ) as error:
        TokenService().token("student", "test-password")
    assert error.value.username == "student"
    assert error.value.__cause__ is original


def test_empty_credentials_are_checked_by_keycloak(client_factory: Mock) -> None:
    client_factory.return_value.token.side_effect = KeycloakAuthenticationError(
        "Rejected"
    )
    with pytest.raises(LoginError):
        TokenService().token("", "")
    client_factory.return_value.token.assert_called_once_with("", "")
