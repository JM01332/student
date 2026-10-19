"""GraphQL-Mutationen mit Attrappen statt Write-Service und Keycloak prüfen."""

lazy from unittest.mock import Mock

import pytest
lazy from pytest_mock import MockerFixture

from student.graphql_api.schema import schema
from student.security import LoginError, Role, User
from student.service import EmailExistsError

NEUE_ID = 1000
TOKEN_LAUFZEIT = 1800
PASSWORD = "p"  # ruff: ignore[hardcoded-password-string]

CREATE = """
mutation {
  create(studentInput: {
    matrikelnummer: "999999", nachname: "Graph", vorname: "Gustav",
    email: "gustav@h-ka.de", username: "gustav",
    adresse: { plz: "PLZ", ort: "Karlsruhe" },
    pruefungsleistungen: [{ modul: "Softwareengineering", note: "1.3",
      semester: "WS 2026/27" }]
  }) { id }
}
"""
LOGIN = (
    'mutation { login(username: "admin", password: "' + PASSWORD + '") '
    "{ token expiresIn roles } }"
)


def _user(*roles: Role) -> User:
    return User(
        username="admin",
        email="admin@acme.com",
        nachname="Admin",
        vorname="Student",
        roles=list(roles),
    )


@pytest.fixture
def write_service(mocker: MockerFixture) -> Mock:
    """StudentWriteService im Modul schema; create liefert ein DTO mit neuer ID."""
    mock = mocker.patch("student.graphql_api.schema._write_service")
    mock.create.return_value.id = NEUE_ID
    return mock


@pytest.fixture(autouse=True)
def token_service(mocker: MockerFixture) -> Mock:
    """TokenService im Modul schema ersetzen; Standard: Benutzer mit Rolle admin."""
    mock = mocker.patch("student.graphql_api.schema._token_service")
    mock.get_user_from_request.return_value = _user(Role.ADMIN)
    mock.get_user_from_token.return_value = _user(Role.ADMIN)
    return mock


def _execute(query: str, mocker: MockerFixture) -> dict:
    """Mutation ohne HTTP direkt gegen das Schema ausführen."""
    result = schema.execute_sync(query, context_value={"request": mocker.Mock()})
    return {"data": result.data, "errors": result.errors}


def test_create(write_service: Mock, mocker: MockerFixture) -> None:
    """Gültige Daten: pydantic validiert, der Service legt an, Ergebnis ist die ID."""
    result = _execute(CREATE.replace("PLZ", "76133"), mocker)

    assert result["errors"] is None
    assert result["data"] == {"create": {"id": NEUE_ID}}
    student = write_service.create.call_args.kwargs["student"]
    assert student.username == "gustav"
    assert student.adresse.ort == "Karlsruhe"
    assert str(student.pruefungsleistungen[0].note) == "1.3"


def test_create_ungueltige_daten(write_service: Mock, mocker: MockerFixture) -> None:
    """Ungültige PLZ: Fehler aus pydantic, der Service wird nicht aufgerufen."""
    result = _execute(CREATE.replace("PLZ", "7"), mocker)

    assert result["data"] is None
    assert "adresse.plz" in result["errors"][0].message
    write_service.create.assert_not_called()


def test_create_ohne_admin(
    write_service: Mock, token_service: Mock, mocker: MockerFixture
) -> None:
    """Ohne Rolle admin wird nicht angelegt (wie beim REST-POST)."""
    token_service.get_user_from_request.return_value = _user(Role.STUDENT)

    result = _execute(CREATE.replace("PLZ", "76133"), mocker)

    assert result["data"] is None
    assert len(result["errors"]) == 1
    write_service.create.assert_not_called()


def test_create_email_existiert(write_service: Mock, mocker: MockerFixture) -> None:
    """Fehler aus dem Service erscheinen mit ihrer Meldung unter errors."""
    write_service.create.side_effect = EmailExistsError("gustav@h-ka.de")

    result = _execute(CREATE.replace("PLZ", "76133"), mocker)

    assert result["data"] is None
    assert "gustav@h-ka.de" in result["errors"][0].message


def test_login(token_service: Mock, mocker: MockerFixture) -> None:
    """Login liefert Token, echte Laufzeit in Sekunden und Rollen."""
    token_service.token.return_value = {
        "access_token": "test-access",
        "expires_in": TOKEN_LAUFZEIT,
    }

    result = _execute(LOGIN, mocker)

    assert result["data"] == {
        "login": {
            "token": "test-access",
            "expiresIn": TOKEN_LAUFZEIT,
            "roles": ["ADMIN"],
        }
    }
    token_service.token.assert_called_once_with(username="admin", password=PASSWORD)


def test_login_falsch(token_service: Mock, mocker: MockerFixture) -> None:
    """Falsche Zugangsdaten ergeben einen Fehler statt Daten."""
    token_service.token.side_effect = LoginError(username="admin")

    result = _execute(LOGIN, mocker)

    assert result["data"] is None
    assert "admin" in result["errors"][0].message
