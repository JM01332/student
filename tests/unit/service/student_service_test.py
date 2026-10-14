"""Unit-Tests für StudentService mit Mocks statt Repository und Session."""

from decimal import Decimal
lazy from unittest.mock import Mock

import pytest
lazy from pytest_mock import MockerFixture

from student.entity import Adresse, Pruefungsleistung, Student
from student.repository import StudentRepository
from student.repository.pageable import Pageable
from student.service import NotFoundError, StudentService

NICHT_VORHANDENE_ID = 999999
"""ID, zu der das Repository-Mock nichts findet."""


@pytest.fixture
def repo_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für StudentRepository, die nur die Methoden der Klasse kennt."""
    return mocker.Mock(spec=StudentRepository)


@pytest.fixture
def session_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für die Session, die `with Session() as session:` zurückliefert."""
    session = mocker.Mock()
    # "Session" im Modul student_service durch eine Attrappe ersetzen, die als
    # Context Manager bei __enter__ die Session-Attrappe liefert
    mocker.patch(
        "student.service.student_service.Session",
        return_value=mocker.MagicMock(
            __enter__=lambda _self: session,
            __exit__=lambda _self, _exc_type, _exc, _tb: None,
        ),
    )
    return session


@pytest.fixture
def service(repo_mock: Mock) -> StudentService:
    """Service mit der Attrappe statt des echten Repositorys."""
    return StudentService(repo=repo_mock)


def _student_entity() -> Student:
    """Student-Entity mit Adresse und einer Prüfungsleistung als Testdaten."""
    student = Student(
        id=1,
        matrikelnummer="123456",
        nachname="Mocktest",
        vorname="Max",
        username="mocktest",
        email="mock@h-ka.de",
        adresse=None,
        pruefungsleistungen=[],
        erzeugt=None,
        aktualisiert=None,
    )
    student.adresse = Adresse(
        plz="11111",
        ort="Mockort",
        id=1,
        student_id=1,
        student=None,
    )
    student.pruefungsleistungen.append(
        Pruefungsleistung(
            modul="Softwareengineering",
            note=Decimal("1.3"),
            semester="WS 2026/27",
            id=1,
            student_id=1,
            student=None,
        ),
    )
    return student


def test_find_by_id(
    service: StudentService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Die Suche mit der ID liefert ein DTO mit den Daten der Entity."""
    # Arrange
    repo_mock.find_by_id.return_value = _student_entity()

    # Act
    student = service.find_by_id(student_id=1)

    # Assert
    assert student is not None
    assert student.id == 1
    assert student.nachname == "Mocktest"
    assert student.adresse is not None
    assert student.adresse.ort == "Mockort"
    assert [p.note for p in student.pruefungsleistungen] == [Decimal("1.3")]
    repo_mock.find_by_id.assert_called_once_with(student_id=1, session=session_mock)
    session_mock.commit.assert_called_once()


def test_find_by_id_nicht_vorhanden(
    service: StudentService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Die Suche mit der ID wirft NotFoundError, wenn das Repository nichts findet."""
    repo_mock.find_by_id.return_value = None

    # pytest.raises: der Test ist nur erfolgreich, wenn die Exception geworfen wird
    with pytest.raises(NotFoundError) as err:
        service.find_by_id(student_id=NICHT_VORHANDENE_ID)

    assert err.value.student_id == NICHT_VORHANDENE_ID
    repo_mock.find_by_id.assert_called_once_with(
        student_id=NICHT_VORHANDENE_ID,
        session=session_mock,
    )
    session_mock.commit.assert_not_called()


@pytest.mark.parametrize(
    ("nachname", "email", "anzahl"),
    [
        (None, None, 5),
        ("mock", None, 2),
        (None, "mock@h-ka.de", 1),
        ("mock", "mock@h-ka.de", 1),
        ("xyz", None, 0),
    ],
)
def test_count(
    repo_mock: Mock,
    session_mock: Mock,
    nachname: str | None,
    email: str | None,
    anzahl: int,
) -> None:
    """Die Zählung reicht Filter weiter und liefert auch 0 ohne NotFoundError."""
    service = StudentService(repo=repo_mock)
    repo_mock.count.return_value = anzahl

    result = service.count(nachname=nachname, email=email)

    assert result == anzahl
    repo_mock.count.assert_called_once_with(
        nachname=nachname,
        email=email,
        session=session_mock,
    )
    session_mock.commit.assert_called_once()


def test_find(
    service: StudentService,
    repo_mock: Mock,
    session_mock: Mock,
) -> None:
    """Die Suche gibt die Suchparameter weiter und liefert DTOs der Entities."""
    repo_mock.find.return_value = [_student_entity()]

    studenten = service.find(nachname="mock", email=None)

    assert [student.nachname for student in studenten] == ["Mocktest"]
    repo_mock.find.assert_called_once_with(
        nachname="mock",
        email=None,
        pageable=None,
        session=session_mock,
    )
    session_mock.commit.assert_called_once()


@pytest.mark.parametrize("size", [2, 0])
def test_find_mit_pagination(
    service: StudentService,
    repo_mock: Mock,
    session_mock: Mock,
    size: int,
) -> None:
    """Seiteneinteilung und beide Filter werden bei der DTO-Suche weitergegeben."""
    pageable = Pageable(number=1, size=size)
    repo_mock.find.return_value = [_student_entity()]

    studenten = service.find(nachname="mock", email="mock@h-ka.de", pageable=pageable)

    assert [student.nachname for student in studenten] == ["Mocktest"]
    repo_mock.find.assert_called_once_with(
        nachname="mock",
        email="mock@h-ka.de",
        pageable=pageable,
        session=session_mock,
    )
    session_mock.commit.assert_called_once()


@pytest.mark.parametrize("pageable", [None, Pageable(number=1, size=2)])
def test_find_ohne_treffer(
    service: StudentService,
    repo_mock: Mock,
    session_mock: Mock,
    pageable: Pageable | None,
) -> None:
    """Die Suche wirft NotFoundError, wenn das Repository nichts findet."""
    repo_mock.find.return_value = []

    with pytest.raises(NotFoundError) as err:
        service.find(nachname="xyz", email=None, pageable=pageable)

    assert err.value.nachname == "xyz"
    repo_mock.find.assert_called_once_with(
        nachname="xyz", email=None, pageable=pageable, session=session_mock
    )
    session_mock.commit.assert_not_called()
