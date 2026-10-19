"""GraphQL-Resolver mit Attrappen statt Service und Keycloak prüfen."""

lazy from unittest.mock import Mock

import pytest
lazy from pytest_mock import MockerFixture

from student.graphql_api.schema import schema
from student.security import Role, User
from student.service import ForbiddenError, NotFoundError, StudentDTO

STUDENT_ID = 20
QUERY_STUDENT = f'{{ student(studentId: "{STUDENT_ID}") {{ id nachname username }} }}'
QUERY_STUDENTEN = (
    '{ studenten(suchparameter: {nachname: "muster", email: null}) { id } }'
)


def _user(*roles: Role) -> User:
    return User(
        username="erika",
        email="erika@h-ka.de",
        nachname="Musterfrau",
        vorname="Erika",
        roles=list(roles),
    )


def _dto(student_id: int = STUDENT_ID) -> StudentDTO:
    return StudentDTO(
        id=student_id,
        version=0,
        matrikelnummer="654321",
        nachname="Musterfrau",
        vorname="Erika",
        email="erika@h-ka.de",
        username="erika",
        adresse=None,
        pruefungsleistungen=[],
    )


@pytest.fixture
def service(mocker: MockerFixture) -> Mock:
    """StudentService im Modul schema durch eine Attrappe ersetzen."""
    return mocker.patch("student.graphql_api.schema._service")


@pytest.fixture(autouse=True)
def token_service(mocker: MockerFixture) -> Mock:
    """TokenService im Modul schema ersetzen; Standard: Benutzer mit Rolle admin.

    `autouse=True`: gilt für jeden Test dieser Datei, auch ohne ihn anzufordern.
    """
    mock = mocker.patch("student.graphql_api.schema._token_service")
    mock.get_user_from_request.return_value = _user(Role.ADMIN)
    return mock


def _execute(query: str, mocker: MockerFixture) -> dict:
    """Query ohne HTTP direkt gegen das Schema ausführen."""
    result = schema.execute_sync(query, context_value={"request": mocker.Mock()})
    return {"data": result.data, "errors": result.errors}


def test_student(service: Mock, mocker: MockerFixture) -> None:
    """Gefundene Daten werden mit den angefragten Feldern geliefert."""
    service.find_by_id.return_value = _dto()

    result = _execute(QUERY_STUDENT, mocker)

    assert result["errors"] is None
    assert result["data"] == {
        "student": {"id": STUDENT_ID, "nachname": "Musterfrau", "username": "erika"}
    }
    assert service.find_by_id.call_args.kwargs["student_id"] == STUDENT_ID


def test_student_nicht_gefunden(service: Mock, mocker: MockerFixture) -> None:
    """Eine unbekannte ID ergibt null ohne Fehler (wie im Beispielprojekt)."""
    service.find_by_id.side_effect = NotFoundError(student_id=STUDENT_ID)

    result = _execute(QUERY_STUDENT, mocker)

    assert result["errors"] is None
    assert result["data"] == {"student": None}


def test_student_fremder_datensatz(service: Mock, mocker: MockerFixture) -> None:
    """Ein verbotener Zugriff erscheint als GraphQL-Fehler unter errors."""
    service.find_by_id.side_effect = ForbiddenError

    result = _execute(QUERY_STUDENT, mocker)

    assert result["data"] == {"student": None}
    assert len(result["errors"]) == 1


def test_studenten_als_admin(service: Mock, mocker: MockerFixture) -> None:
    """Admin sucht mit den Suchparametern; der Service bekommt sie unverändert."""
    service.find.return_value = [_dto(1), _dto(STUDENT_ID)]

    result = _execute(QUERY_STUDENTEN, mocker)

    assert result["data"] == {"studenten": [{"id": 1}, {"id": STUDENT_ID}]}
    service.find.assert_called_once_with(nachname="muster", email=None)


def test_studenten_ohne_admin(
    service: Mock, token_service: Mock, mocker: MockerFixture
) -> None:
    """Ohne Rolle admin: leere Liste, der Service wird nicht gefragt."""
    token_service.get_user_from_request.return_value = _user(Role.STUDENT)

    result = _execute(QUERY_STUDENTEN, mocker)

    assert result["data"] == {"studenten": []}
    service.find.assert_not_called()


def test_studenten_ohne_treffer(service: Mock, mocker: MockerFixture) -> None:
    """Keine Treffer: leere Liste statt Fehler."""
    service.find.side_effect = NotFoundError(nachname="muster")

    result = _execute(QUERY_STUDENTEN, mocker)

    assert result["errors"] is None
    assert result["data"] == {"studenten": []}
