"""Repository-Tests mit Session-Mock und PostgreSQL-SQL ohne Datenbankzugriff."""

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
lazy from pytest_mock import MockerFixture

from student.repository import StudentRepository
from student.repository.pageable import Pageable


@pytest.mark.parametrize(
    ("pageable", "pagination_sql"),
    [
        (None, None),
        (Pageable(number=0, size=2), "LIMIT 2 OFFSET 0"),
        (Pageable(number=1, size=2), "LIMIT 2 OFFSET 2"),
        (Pageable(number=3, size=2), "LIMIT 2 OFFSET 6"),
        (Pageable(number=4, size=0), None),
    ],
)
def test_find_pagination(
    mocker: MockerFixture,
    pageable: Pageable | None,
    pagination_sql: str | None,
) -> None:
    """Seiten begrenzen die SQL-Abfrage bei stabiler Sortierung nach ID."""
    session = mocker.Mock(spec=Session)
    session.scalars.return_value.all.return_value = []
    repo = StudentRepository()

    if pageable is None:
        result = repo.find(nachname=None, email=None, session=session)
    else:
        result = repo.find(
            nachname=None, email=None, session=session, pageable=pageable
        )

    assert result == []
    session.scalars.assert_called_once()
    statement = session.scalars.call_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "ORDER BY student.id" in sql
    if pagination_sql is None:
        assert "LIMIT" not in sql
        assert "OFFSET" not in sql
    else:
        assert pagination_sql in sql


def test_find_pagination_mit_suchfiltern(mocker: MockerFixture) -> None:
    """Beide Suchfilter bleiben vor der Seiteneinteilung wirksam."""
    session = mocker.Mock(spec=Session)
    studenten = [mocker.sentinel.student]
    session.scalars.return_value.all.return_value = studenten

    result = StudentRepository().find(
        nachname="Muster",
        email="TEST@H-KA.DE",
        session=session,
        pageable=Pageable(number=1, size=2),
    )

    assert result is studenten
    session.scalars.assert_called_once()
    statement = session.scalars.call_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )
    assert "student.nachname ILIKE" in sql
    assert "Muster" in sql
    assert "AND lower(student.email) = 'test@h-ka.de'" in sql
    assert "ORDER BY student.id" in sql
    assert "LIMIT 2 OFFSET 2" in sql
