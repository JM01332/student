"""Unit-Tests für StudentWriteService mit Mocks statt Repository und Session."""

from decimal import Decimal
lazy from unittest.mock import Mock

import pytest
lazy from pytest_mock import MockerFixture

from student.entity import Adresse, Pruefungsleistung, Student
from student.repository import StudentRepository
from student.security import UserService
from student.service import (
    EmailExistsError,
    MatrikelnummerExistsError,
    NotFoundError,
    StudentWriteService,
    VersionOutdatedError,
)

NEUE_ID = 1000
"""ID, die die DB beim Anlegen vergibt (IDENTITY START WITH 1000)."""


@pytest.fixture
def repo_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für StudentRepository; Email und Matrikelnummer sind noch frei."""
    repo = mocker.Mock(spec=StudentRepository)
    repo.exists_email.return_value = False
    repo.exists_matrikelnummer.return_value = False
    repo.exists_email_other_id.return_value = False
    repo.exists_matrikelnummer_other_id.return_value = False
    return repo


@pytest.fixture
def session_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für die Session, die `with Session() as session:` zurückliefert."""
    session = mocker.Mock()
    mocker.patch(
        "student.service.student_write_service.Session",
        return_value=mocker.MagicMock(
            __enter__=lambda _self: session,
            __exit__=lambda _self, _exc_type, _exc, _tb: None,
        ),
    )
    return session


@pytest.fixture
def user_service_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für UserService; Username und Email sind in Keycloak noch frei."""
    user_service = mocker.Mock(spec=UserService)
    user_service.username_exists.return_value = False
    user_service.email_exists.return_value = False
    return user_service


@pytest.fixture
def service(repo_mock: Mock, user_service_mock: Mock) -> StudentWriteService:
    """Write-Service mit Attrappen statt Repository und Keycloak."""
    return StudentWriteService(repo=repo_mock, user_service=user_service_mock)


def _neuer_student() -> Student:
    """Neuer Studierender ohne ID, wie ihn StudentModel.to_student() liefert."""
    student = Student(
        id=None,
        matrikelnummer="999999",
        nachname="Test",
        vorname="Theo",
        username="theo",
        email="theo.test@h-ka.de",
        adresse=None,
        pruefungsleistungen=[],
        erzeugt=None,
        aktualisiert=None,
    )
    student.adresse = Adresse(
        plz="76133",
        ort="Karlsruhe",
        id=None,
        student_id=None,
        student=None,
    )
    student.pruefungsleistungen.append(
        Pruefungsleistung(
            modul="Softwareengineering",
            note=Decimal("1.3"),
            semester="WS 2026/27",
            id=None,
            student_id=None,
            student=None,
        ),
    )
    return student


def _mit_id(student: Student, session: Mock) -> Student:  # ruff: ignore[unused-function-argument]
    """Nachbildung von repo.create(): Die DB vergibt die ID."""
    student.id = NEUE_ID
    return student


def test_create(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Ein neuer Studierender wird gespeichert und als DTO mit neuer ID geliefert."""
    repo_mock.create.side_effect = _mit_id
    student = _neuer_student()

    student_dto = service.create(student=student)

    assert student_dto.id == NEUE_ID
    assert student_dto.nachname == "Test"
    repo_mock.create.assert_called_once_with(student=student, session=session_mock)
    session_mock.commit.assert_called_once()


def test_create_email_existiert(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Eine bereits vorhandene Email verhindert das Speichern."""
    repo_mock.exists_email.return_value = True

    with pytest.raises(EmailExistsError) as err:
        service.create(student=_neuer_student())

    assert err.value.email == "theo.test@h-ka.de"
    repo_mock.create.assert_not_called()
    session_mock.commit.assert_not_called()


def test_create_matrikelnummer_existiert(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Eine bereits vorhandene Matrikelnummer verhindert das Speichern."""
    repo_mock.exists_matrikelnummer.return_value = True

    with pytest.raises(MatrikelnummerExistsError) as err:
        service.create(student=_neuer_student())

    assert err.value.matrikelnummer == "999999"
    repo_mock.create.assert_not_called()
    session_mock.commit.assert_not_called()


VORHANDENE_ID = 1001
VERSION = 2


def _student_db() -> Student:
    """Vorhandener Studierender, wie ihn repo.find_by_id() aus der DB liefert."""
    student = _neuer_student()
    student.id = VORHANDENE_ID
    student.version = VERSION
    return student


def _geaenderter_student() -> Student:
    """Neue Daten, wie sie StudentUpdateModel.to_student() liefert."""
    return Student(
        id=None,
        matrikelnummer="888888",
        nachname="Neu",
        vorname="Nora",
        username=None,
        email="nora.neu@h-ka.de",
        adresse=None,
        pruefungsleistungen=[],
        erzeugt=None,
        aktualisiert=None,
    )


def test_update(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Die neuen Daten werden übernommen; das DTO hat die erhöhte Version."""
    student_db = _student_db()
    repo_mock.find_by_id.return_value = student_db
    repo_mock.update.return_value = student_db

    student_dto = service.update(
        student=_geaenderter_student(), student_id=VORHANDENE_ID, version=VERSION
    )

    assert student_dto.id == VORHANDENE_ID
    assert student_dto.nachname == "Neu"
    assert student_dto.matrikelnummer == "888888"
    assert student_dto.version == VERSION + 1
    repo_mock.update.assert_called_once_with(student=student_db, session=session_mock)
    session_mock.commit.assert_called_once()


def test_update_gleiche_email_und_matrikelnummer(
    service: StudentWriteService,
    repo_mock: Mock,
) -> None:
    """Unveränderte Email und Matrikelnummer werden nicht erneut geprüft."""
    student_db = _student_db()
    repo_mock.find_by_id.return_value = student_db
    repo_mock.update.return_value = student_db

    service.update(student=_neuer_student(), student_id=VORHANDENE_ID, version=VERSION)

    repo_mock.exists_email_other_id.assert_not_called()
    repo_mock.exists_matrikelnummer_other_id.assert_not_called()


def test_update_nicht_gefunden(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Zu einer nicht vorhandenen ID gibt es NotFoundError."""
    repo_mock.find_by_id.return_value = None

    with pytest.raises(NotFoundError) as err:
        service.update(
            student=_geaenderter_student(), student_id=VORHANDENE_ID, version=VERSION
        )

    assert err.value.student_id == VORHANDENE_ID
    session_mock.commit.assert_not_called()


def test_update_version_veraltet(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Eine ältere Version als in der DB verhindert das Überschreiben."""
    repo_mock.find_by_id.return_value = _student_db()
    veraltet = VERSION - 1

    with pytest.raises(VersionOutdatedError) as err:
        service.update(
            student=_geaenderter_student(), student_id=VORHANDENE_ID, version=veraltet
        )

    assert err.value.version == veraltet
    repo_mock.update.assert_not_called()
    session_mock.commit.assert_not_called()


def test_update_email_existiert(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Die Email eines anderen Studierenden darf nicht übernommen werden."""
    repo_mock.find_by_id.return_value = _student_db()
    repo_mock.exists_email_other_id.return_value = True

    with pytest.raises(EmailExistsError) as err:
        service.update(
            student=_geaenderter_student(), student_id=VORHANDENE_ID, version=VERSION
        )

    assert err.value.email == "nora.neu@h-ka.de"
    repo_mock.update.assert_not_called()
    session_mock.commit.assert_not_called()


def test_update_matrikelnummer_existiert(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Die Matrikelnummer eines anderen Studierenden darf nicht übernommen werden."""
    repo_mock.find_by_id.return_value = _student_db()
    repo_mock.exists_matrikelnummer_other_id.return_value = True

    with pytest.raises(MatrikelnummerExistsError) as err:
        service.update(
            student=_geaenderter_student(), student_id=VORHANDENE_ID, version=VERSION
        )

    assert err.value.matrikelnummer == "888888"
    repo_mock.update.assert_not_called()
    session_mock.commit.assert_not_called()


def test_delete_by_id(
    service: StudentWriteService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Das Löschen wird an das Repository weitergereicht und committet."""
    service.delete_by_id(student_id=VORHANDENE_ID)

    repo_mock.delete_by_id.assert_called_once_with(
        student_id=VORHANDENE_ID, session=session_mock
    )
    session_mock.commit.assert_called_once()
