"""Token-Ausstellung und -Auswertung ohne Keycloak-Verbindung prüfen."""

lazy from unittest.mock import Mock

import pytest
from fastapi import Request
from jwcrypto.common import JWException
from keycloak import KeycloakAuthenticationError, KeycloakOperationError
lazy from pytest_mock import MockerFixture

from student.config.keycloak import KeycloakConfig
from student.security import AuthorizationError, LoginError, Role, TokenService

# Ausschließlich Dummy für den gemockten Client.
TEST_SECRET = "test-secret"  # ruff: ignore[hardcoded-password-string]
TEST_ACCESS = "test-access"


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


@pytest.fixture
def claims(client_factory: Mock) -> dict[str, object]:
    """Benutzer-Claims und Client-Rollen für die Token-Auswertung bereitstellen."""
    client_factory.return_value.client_id = "test-client"
    result = {
        "preferred_username": "student",
        "email": "student@example.com",
        "family_name": "Mustermann",
        "given_name": "Max",
        "resource_access": {"test-client": {"roles": ["student"]}},
    }
    client_factory.return_value.decode_token.return_value = result
    return result


@pytest.mark.parametrize(
    ("roles", "expected"),
    [
        (["student"], [Role.STUDENT]),
        (["admin", "student"], [Role.ADMIN, Role.STUDENT]),
        (["ADMIN", "Student"], [Role.ADMIN, Role.STUDENT]),
        ([], []),
    ],
)
def test_user_from_token(
    client_factory: Mock,
    claims: dict[str, object],
    roles: list[str],
    expected: list[Role],
) -> None:
    claims["resource_access"] = {
        "test-client": {"roles": roles},
        "other-client": {"roles": ["unknown"]},
    }
    claims["realm_access"] = {"roles": ["unknown"]}
    user = TokenService().get_user_from_token("test-access")
    assert user.username == "student"
    assert user.email == "student@example.com"
    assert user.nachname == "Mustermann"
    assert user.vorname == "Max"
    assert user.roles == expected
    assert user.password is None
    client_factory.return_value.decode_token.assert_called_once_with(token=TEST_ACCESS)


@pytest.mark.parametrize(
    "claim",
    ["preferred_username", "email", "family_name", "given_name", "resource_access"],
)
def test_missing_user_claim(
    client_factory: Mock, claims: dict[str, object], claim: str
) -> None:
    del claims[claim]
    with pytest.raises(AuthorizationError) as error:
        TokenService().get_user_from_token("test-access")
    assert isinstance(error.value.__cause__, KeyError)
    client_factory.return_value.decode_token.assert_called_once_with(token=TEST_ACCESS)


@pytest.mark.parametrize(
    "resource_access",
    [
        None,
        [],
        {},
        {"other-client": {"roles": ["admin"]}},
        {"test-client": None},
        {"test-client": {}},
        {"test-client": {"roles": None}},
        {"test-client": {"roles": ["unknown"]}},
    ],
)
def test_invalid_client_roles(
    client_factory: Mock, claims: dict[str, object], resource_access: object
) -> None:
    claims["resource_access"] = resource_access
    with pytest.raises(AuthorizationError) as error:
        TokenService().get_user_from_token("test-access")
    assert isinstance(error.value.__cause__, (KeyError, TypeError))
    client_factory.return_value.decode_token.assert_called_once_with(token=TEST_ACCESS)


@pytest.mark.parametrize("error_type", [JWException, KeyError, TypeError, ValueError])
def test_token_decode_error(client_factory: Mock, error_type: type[Exception]) -> None:
    original = error_type("Invalid token")
    client_factory.return_value.decode_token.side_effect = original
    with pytest.raises(AuthorizationError) as error:
        TokenService().get_user_from_token("test-access")
    assert error.value.__cause__ is original


def test_invalid_decoded_token(client_factory: Mock) -> None:
    client_factory.return_value.decode_token.return_value = None
    with pytest.raises(AuthorizationError) as error:
        TokenService().get_user_from_token("test-access")
    assert isinstance(error.value.__cause__, TypeError)


@pytest.mark.parametrize(
    "header",
    [
        "Bearer test-access",
        "bearer test-access",
        "BEARER test-access",
        "bEaReR test-access",
        "  Bearer   test-access  ",
        "Bearer\ttest-access",
    ],
)
@pytest.mark.usefixtures("claims")
def test_user_from_request(client_factory: Mock, header: str) -> None:
    request = Request({
        "type": "http",
        "headers": [(b"authorization", header.encode("ascii"))],
    })
    user = TokenService().get_user_from_request(request)
    assert user.username == "student"
    assert user.email == "student@example.com"
    assert user.roles == [Role.STUDENT]
    client_factory.return_value.decode_token.assert_called_once_with(token=TEST_ACCESS)


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        "   ",
        "Bearer",
        "Bearer   ",
        "test-access",
        "Basic test-access",
        "Bearer test-access extra",
        "Bearertest-access",
    ],
)
def test_invalid_authorization_header(client_factory: Mock, header: str | None) -> None:
    headers = [] if header is None else [(b"authorization", header.encode("ascii"))]
    request = Request({"type": "http", "headers": headers})
    with pytest.raises(AuthorizationError):
        TokenService().get_user_from_request(request)
    client_factory.return_value.decode_token.assert_not_called()


def test_request_with_invalid_token(client_factory: Mock) -> None:
    original = JWException("Invalid token")
    client_factory.return_value.decode_token.side_effect = original
    request = Request({
        "type": "http",
        "headers": [(b"authorization", b"Bearer test-access")],
    })
    with pytest.raises(AuthorizationError) as error:
        TokenService().get_user_from_request(request)
    assert error.value.__cause__ is original
    client_factory.return_value.decode_token.assert_called_once_with(token=TEST_ACCESS)
