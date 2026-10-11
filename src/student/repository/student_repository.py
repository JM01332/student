"""Repository für den Datenzugriff auf Studierende."""

from typing import Final
lazy from collections.abc import Sequence

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload
lazy from sqlalchemy.orm import Session

from student.entity import Student

__all__ = ["StudentRepository"]


class StudentRepository:
    """Repository-Klasse mit Lesezugriff auf Studierende in der DB."""

    def find_by_id(self, student_id: int, session: Session) -> Student | None:
        """Suche mit der Student-ID in der DB.

        Die Adresse wird per JOIN mitgeladen (1:1), die Prüfungsleistungen mit
        einer zweiten Abfrage per `IN` (1:N), damit kein N+1-Problem entsteht.

        :param student_id: ID des gesuchten Studierenden
        :param session: Session für SQLAlchemy
        :return: Der gefundene Studierende oder None
        :rtype: Student | None
        """
        logger.debug("student_id={}", student_id)
        statement: Final = (
            select(Student)
            .options(
                joinedload(Student.adresse),
                selectinload(Student.pruefungsleistungen),
            )
            .where(Student.id == student_id)
        )
        student: Final = session.scalar(statement)
        logger.debug("{}", student)
        return student

    def find(
        self,
        nachname: str | None,
        email: str | None,
        session: Session,
    ) -> Sequence[Student]:
        """Suche mit optionalen Suchparametern in der DB.

        :param nachname: Teil des Nachnamens, ohne Groß-/Kleinschreibung
        :param email: Emailadresse, ohne Groß-/Kleinschreibung
        :param session: Session für SQLAlchemy
        :return: Gefundene Studierende, nach ID sortiert, ggf. leer
        :rtype: Sequence[Student]
        """
        logger.debug("nachname={}, email={}", nachname, email)
        statement = select(Student).options(
            joinedload(Student.adresse),
            selectinload(Student.pruefungsleistungen),
        )
        if nachname is not None:
            # ILIKE: wie LIKE, aber ohne Unterscheidung von Groß-/Kleinschreibung
            statement = statement.where(Student.nachname.ilike(f"%{nachname}%"))
        if email is not None:
            statement = statement.where(func.lower(Student.email) == email.lower())
        studenten: Final = session.scalars(statement.order_by(Student.id)).all()
        logger.debug("{}", studenten)
        return studenten
