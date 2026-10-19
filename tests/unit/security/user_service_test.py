"""UserService ohne Keycloak-Verbindung mit nachgebautem KeycloakAdmin prüfen."""

lazy from unittest.mock import Mock

import pytest
from keycloak import KeycloakConnectionError
lazy from pytest_mock import MockerFixture

from student.config.keycloak import KeycloakAdminConfig
from student.security import Role, User, UserService

# Ausschließlich Dummies für den gemockten Client.
TEST_SECRET = "test-secret"  # ruff: ignore[hardcoded-password-string]
TEST_PASSWORD = "test-password"  # ruff: ignore[hardcoded-password-string]
CLIENT_UUID = "client-uuid"
ROLLE_STUDENT = {"id": "rolle-1", "name": "student"}


@pytest.fixture
def admin_factory(mocker: MockerFixture) -> Mock:
    """KeycloakAdmin und Konfiguration ohne echte Zugangsdaten bereitstellen."""
    mocker.patch(
        "student.security.user_service.keycloak_admin_config",
        KeycloakAdminConfig(
            server_url="https://keycloak.example/",
            realm_name="test-realm",
            client_id="test-client",
            client_secret_key=TEST_SECRET,
            verify="test-certificate.crt",
            username="admin",
            password=TEST_PASSWORD,
        ),
    )
    factory = mocker.patch("student.security.user_service.KeycloakAdmin", autospec=True)
    admin = factory.return_value
    admin.get_client_id.return_value = CLIENT_UUID
    admin.get_client_roles.return_value = [
        {"id": "rolle-0", "name": "admin"},
        ROLLE_STUDENT,
    ]
    return factory


def test_initialization(admin_factory: Mock) -> None:
    """Client-UUID und Rolle student werden einmal beim Erzeugen ermittelt."""
    service = UserService()

    admin_factory.assert_called_once_with(
        server_url="https://keycloak.example/",
        username="admin",
        password=TEST_PASSWORD,
        realm_name="test-realm",
        client_id="test-client",
        client_secret_key=TEST_SECRET,
        verify="test-certificate.crt",
    )
    admin_factory.return_value.get_client_id.assert_called_once_with("test-client")
    admin_factory.return_value.get_client_roles.assert_called_once_with(
        client_id=CLIENT_UUID
    )
    assert service.client_uuid == CLIENT_UUID
    assert service.rolle_student == ROLLE_STUDENT


def test_initialization_ohne_keycloak(admin_factory: Mock) -> None:
    """Ohne Keycloak startet die Anwendung trotzdem (wie im Beispielprojekt)."""
    admin_factory.return_value.get_client_id.side_effect = KeycloakConnectionError

    service = UserService()

    assert service.client_uuid is None
    assert service.rolle_student is None


@pytest.mark.parametrize(("user_id", "erwartet"), [("user-1", True), (None, False)])
def test_username_exists(
    admin_factory: Mock, user_id: str | None, *, erwartet: bool
) -> None:
    admin_factory.return_value.get_user_id.return_value = user_id

    assert UserService().username_exists("erika") is erwartet
    admin_factory.return_value.get_user_id.assert_called_once_with("erika")


@pytest.mark.parametrize(
    ("users", "erwartet"), [([{"id": "user-1"}], True), ([], False)]
)
def test_email_exists(
    admin_factory: Mock, users: list[dict[str, str]], *, erwartet: bool
) -> None:
    admin_factory.return_value.get_users.return_value = users

    assert UserService().email_exists("erika@h-ka.de") is erwartet
    admin_factory.return_value.get_users.assert_called_once_with(
        query={"email": "erika@h-ka.de"}
    )


def test_create_user(admin_factory: Mock) -> None:
    """Der Benutzer wird mit Passwort angelegt und bekommt die Rolle student."""
    admin = admin_factory.return_value
    admin.create_user.return_value = "user-1"
    user = User(
        username="erika",
        email="erika@h-ka.de",
        nachname="Musterfrau",
        vorname="Erika",
        roles=[Role.STUDENT],
        password=TEST_PASSWORD,
    )

    user_id = UserService().create_user(user)

    assert user_id == "user-1"
    admin.create_user.assert_called_once_with(
        payload={
            "username": "erika",
            "email": "erika@h-ka.de",
            "lastName": "Musterfrau",
            "firstName": "Erika",
            "credentials": [{"value": TEST_PASSWORD, "type": "password"}],
            "enabled": True,
        },
        exist_ok=False,
    )
    admin.assign_client_role.assert_called_once_with(
        user_id="user-1", client_id=CLIENT_UUID, roles=[ROLLE_STUDENT]
    )


def test_remove_all_users(admin_factory: Mock) -> None:
    """Alle Benutzer außer admin werden gelöscht."""
    admin = admin_factory.return_value
    admin.get_users.return_value = [
        {"id": "id-admin", "username": "admin"},
        {"id": "id-erika", "username": "erika"},
        {"id": "id-lena", "username": "lena"},
    ]

    UserService().remove_all_users()

    deleted = [call.args[0] for call in admin.delete_user.call_args_list]
    assert deleted == ["id-erika", "id-lena"]
