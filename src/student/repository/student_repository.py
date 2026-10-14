"""Repository für den Datenzugriff auf Studierende."""

from typing import Final
lazy from collections.abc import Sequence

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload
lazy from sqlalchemy.orm import Session

from student.entity import Student
lazy from student.repository.pageable import Pageable

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
        pageable: Pageable | None = None,
    ) -> Sequence[Student]:
        """Suche mit optionalen Suchparametern in der DB.

        :param nachname: Teil des Nachnamens, ohne Groß-/Kleinschreibung
        :param email: Emailadresse, ohne Groß-/Kleinschreibung
        :param session: Session für SQLAlchemy
        :param pageable: Validierte Seiteneinteilung; None oder size=0 für alle Treffer
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
        statement = statement.order_by(Student.id)
        if pageable is not None and pageable.size != 0:
            statement = statement.limit(pageable.size).offset(
                pageable.number * pageable.size
            )
        studenten: Final = session.scalars(statement).all()
        logger.debug("{}", studenten)
        return studenten

    def count(
        self,
        nachname: str | None,
        email: str | None,
        session: Session,
    ) -> int:
        """Zähle alle Treffer der Suche unabhängig von der Seiteneinteilung.

        :param nachname: Teil des Nachnamens, ohne Groß-/Kleinschreibung
        :param email: Emailadresse, ohne Groß-/Kleinschreibung
        :param session: Session für SQLAlchemy
        :return: Gesamtanzahl der passenden Studierenden, ggf. 0
        :rtype: int
        """
        logger.debug("nachname={}, email={}", nachname, email)
        statement = select(func.count()).select_from(Student)
        if nachname is not None:
            statement = statement.where(Student.nachname.ilike(f"%{nachname}%"))
        if email is not None:
            statement = statement.where(func.lower(Student.email) == email.lower())
        count: Final = session.scalar(statement)
        logger.debug("count={}", count)
        return count if count is not None else 0

    def exists_email(self, email: str, session: Session) -> bool:
        """Abfrage, ob es die Emailadresse bereits gibt (ohne Groß-/Kleinschreibung).

        :param email: Emailadresse
        :param session: Session für SQLAlchemy
        :return: True, falls es die Emailadresse bereits gibt, False sonst
        :rtype: bool
        """
        logger.debug("email={}", email)
        statement: Final = (
            select(func.count())
            .select_from(Student)
            .where(func.lower(Student.email) == email.lower())
        )
        anzahl: Final = session.scalar(statement)
        logger.debug("anzahl={}", anzahl)
        return anzahl is not None and anzahl > 0

    def exists_matrikelnummer(self, matrikelnummer: str, session: Session) -> bool:
        """Abfrage, ob es die Matrikelnummer bereits gibt.

        :param matrikelnummer: Matrikelnummer
        :param session: Session für SQLAlchemy
        :return: True, falls es die Matrikelnummer bereits gibt, False sonst
        :rtype: bool
        """
        logger.debug("matrikelnummer={}", matrikelnummer)
        statement: Final = (
            select(func.count())
            .select_from(Student)
            .where(Student.matrikelnummer == matrikelnummer)
        )
        anzahl: Final = session.scalar(statement)
        logger.debug("anzahl={}", anzahl)
        return anzahl is not None and anzahl > 0

    def create(self, student: Student, session: Session) -> Student:
        """Einen neuen Studierenden mit Adresse und Prüfungsleistungen speichern.

        :param student: Die Daten des neuen Studierenden ohne ID
        :param session: Session für SQLAlchemy
        :return: Der neu angelegte Studierende mit generierter ID
        :rtype: Student
        """
        logger.debug(
            "student={}, adresse={}, pruefungsleistungen={}",
            student,
            student.adresse,
            student.pruefungsleistungen,
        )
        # Adresse und Prüfungsleistungen werden per cascade="save-update" mitgespeichert
        session.add(instance=student)
        # flush(): INSERT sofort ausführen, damit die generierte ID vor dem COMMIT
        # bekannt ist (z.B. für den Location-Header)
        session.flush(objects=[student])
        logger.debug("student_id={}", student.id)
        return student
