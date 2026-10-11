"""Unit-Tests für StudentService mit einem Mock statt des echten Repositorys."""

from typing import Any
lazy from unittest.mock import Mock

import pytest
lazy from pytest_mock import MockerFixture

from student.repository import StudentRepository
from student.service import StudentService

STUDENT_MOCK: dict[str, Any] = {
    "id": 1,
    "matrikelnummer": "123456",
    "nachname": "Mocktest",
    "vorname": "Max",
    "email": "mock@h-ka.de",
    "adresse": {"plz": "11111", "ort": "Mockort"},
    "pruefungsleistungen": [],
}


@pytest.fixture
def repo_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für StudentRepository, die nur die Methoden der Klasse kennt."""
    return mocker.Mock(spec=StudentRepository)


@pytest.fixture
def service(repo_mock: Mock) -> StudentService:
    """Service mit der Attrappe statt des echten Repositorys."""
    return StudentService(repo=repo_mock)


def test_find_by_id(service: StudentService, repo_mock: Mock) -> None:
    """Die Suche mit der ID liefert die Daten aus dem Repository."""
    # Arrange
    repo_mock.find_by_id.return_value = STUDENT_MOCK

    # Act
    student = service.find_by_id(student_id=1)

    # Assert
    assert student == STUDENT_MOCK
    repo_mock.find_by_id.assert_called_once_with(1)


def test_find_by_id_nicht_vorhanden(service: StudentService, repo_mock: Mock) -> None:
    """Die Suche mit der ID liefert None, wenn das Repository nichts findet."""
    repo_mock.find_by_id.return_value = None

    student = service.find_by_id(student_id=999)

    assert student is None
    repo_mock.find_by_id.assert_called_once_with(999)


def test_find_reicht_suchparameter_weiter(
    service: StudentService,
    repo_mock: Mock,
) -> None:
    """Die Suche gibt die Suchparameter unverändert an das Repository weiter."""
    repo_mock.find.return_value = [STUDENT_MOCK]

    studenten = service.find(nachname="mock", email=None)

    assert studenten == [STUDENT_MOCK]
    repo_mock.find.assert_called_once_with(nachname="mock", email=None)
