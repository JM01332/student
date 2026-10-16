"""Geschäftslogik zum Schreiben von Studierendendaten."""

from typing import Final

from loguru import logger

from student.repository import Session
from student.service.exceptions import (
    EmailExistsError,
    MatrikelnummerExistsError,
    NotFoundError,
    VersionOutdatedError,
)
from student.service.student_dto import StudentDTO
lazy from student.entity import Student
lazy from student.repository import StudentRepository

__all__ = ["StudentWriteService"]


class StudentWriteService:
    """Service-Klasse mit Geschäftslogik zum Schreiben von Studierendendaten."""

    def __init__(self, repo: StudentRepository) -> None:
        """Konstruktor mit abhängigem StudentRepository."""
        self.repo: StudentRepository = repo

    def create(self, student: Student) -> StudentDTO:
        """Einen neuen Studierenden anlegen.

        :param student: Der neue Studierende ohne ID
        :return: Der neu angelegte Studierende mit generierter ID
        :rtype: StudentDTO
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        :raises MatrikelnummerExistsError: Falls die Matrikelnummer bereits existiert
        """
        logger.debug(
            "student={}, adresse={}, pruefungsleistungen={}",
            student,
            student.adresse,
            student.pruefungsleistungen,
        )
        with Session() as session:
            if self.repo.exists_email(email=student.email, session=session):
                raise EmailExistsError(email=student.email)
            if self.repo.exists_matrikelnummer(
                matrikelnummer=student.matrikelnummer,
                session=session,
            ):
                raise MatrikelnummerExistsError(matrikelnummer=student.matrikelnummer)

            student_db: Final = self.repo.create(student=student, session=session)
            student_dto: Final = StudentDTO.from_student(student_db)
            session.commit()

        logger.debug("student_dto={}", student_dto)
        return student_dto

    def update(self, student: Student, student_id: int, version: int) -> StudentDTO:
        """Daten eines Studierenden ändern.

        :param student: Die neuen Daten
        :param student_id: ID des zu aktualisierenden Studierenden
        :param version: Version für optimistische Synchronisation
        :return: Der aktualisierte Studierende
        :rtype: StudentDTO
        :raises NotFoundError: Falls der zu aktualisierende Studierende nicht existiert
        :raises VersionOutdatedError: Falls die Versionsnummer nicht aktuell ist
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        :raises MatrikelnummerExistsError: Falls die Matrikelnummer bereits existiert
        """
        logger.debug("student_id={}, version={}, {}", student_id, version, student)

        with Session() as session:
            if (
                student_db := self.repo.find_by_id(
                    student_id=student_id,
                    session=session,
                )
            ) is None:
                raise NotFoundError(student_id)
            if student_db.version > version:
                raise VersionOutdatedError(version)

            email: Final = student.email
            if email != student_db.email and self.repo.exists_email_other_id(
                email=email,
                student_id=student_id,
                session=session,
            ):
                raise EmailExistsError(email)

            matrikelnummer: Final = student.matrikelnummer
            if (
                matrikelnummer != student_db.matrikelnummer
                and self.repo.exists_matrikelnummer_other_id(
                    matrikelnummer=matrikelnummer,
                    student_id=student_id,
                    session=session,
                )
            ):
                raise MatrikelnummerExistsError(matrikelnummer)

            student_db.set(student)
            if (
                student_updated := self.repo.update(student=student_db, session=session)
            ) is None:
                raise NotFoundError(student_id)
            student_dto: Final = StudentDTO.from_student(student_updated)
            logger.debug("{}", student_dto)

            session.commit()
            # Die erhöhte Versionsnummer ist erst nach dem COMMIT sichtbar
            student_dto.version += 1
            return student_dto

    def delete_by_id(self, student_id: int) -> None:
        """Einen Studierenden anhand seiner ID löschen.

        Eine nicht vorhandene ID ist kein Fehler: Danach gibt es den Studierenden
        so oder so nicht (idempotentes DELETE).

        :param student_id: ID des zu löschenden Studierenden
        """
        logger.debug("student_id={}", student_id)
        with Session() as session:
            self.repo.delete_by_id(student_id=student_id, session=session)
            session.commit()
