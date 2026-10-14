"""Unit-Tests für StudentWriteService mit Mocks statt Repository und Session."""

from decimal import Decimal
lazy from unittest.mock import Mock

import pytest
lazy from pytest_mock import MockerFixture

from student.entity import Adresse, Pruefungsleistung, Student
from student.repository import StudentRepository
from student.service import (
    EmailExistsError,
    MatrikelnummerExistsError,
    StudentWriteService,
)

NEUE_ID = 1000
"""ID, die die DB beim Anlegen vergibt (IDENTITY START WITH 1000)."""


@pytest.fixture
def repo_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für StudentRepository; Email und Matrikelnummer sind noch frei."""
    repo = mocker.Mock(spec=StudentRepository)
    repo.exists_email.return_value = False
    repo.exists_matrikelnummer.return_value = False
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
def service(repo_mock: Mock) -> StudentWriteService:
    """Write-Service mit der Attrappe statt des echten Repositorys."""
    return StudentWriteService(repo=repo_mock)


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
