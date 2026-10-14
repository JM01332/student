"""Geschäftslogik zum Schreiben von Studierendendaten."""

from typing import Final

from loguru import logger

from student.repository import Session
from student.service.exceptions import EmailExistsError, MatrikelnummerExistsError
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
