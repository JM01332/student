"""Geschäftslogik für Studierende."""

from typing import Final

from loguru import logger

from student.repository import Session
from student.service.student_dto import StudentDTO
lazy from student.repository import StudentRepository

__all__ = ["StudentService"]


class StudentService:
    """Service-Klasse mit Geschäftslogik für Studierende."""

    def __init__(self, repo: StudentRepository) -> None:
        """Konstruktor mit abhängigem StudentRepository."""
        self.repo: StudentRepository = repo

    def find_by_id(self, student_id: int) -> StudentDTO | None:
        """Einen Studierenden anhand der ID suchen.

        :param student_id: ID des gesuchten Studierenden
        :return: Daten des Studierenden oder None, falls es die ID nicht gibt
        :rtype: StudentDTO | None
        """
        logger.debug("student_id={}", student_id)
        # "with" schließt die Session am Ende des Blocks, auch bei einem Fehler
        with Session() as session:
            student: Final = self.repo.find_by_id(
                student_id=student_id,
                session=session,
            )
            if student is None:
                return None
            # DTO erzeugen, solange die Session noch offen ist
            student_dto: Final = StudentDTO.from_student(student)
            session.commit()

        logger.debug("{}", student_dto)
        return student_dto

    def find(self, nachname: str | None, email: str | None) -> list[StudentDTO]:
        """Studierende mit optionalen Suchparametern suchen.

        :param nachname: Teil des Nachnamens
        :param email: Emailadresse
        :return: Liste der gefundenen Studierenden, ggf. leer
        :rtype: list[StudentDTO]
        """
        logger.debug("nachname={}, email={}", nachname, email)
        with Session() as session:
            studenten: Final = self.repo.find(
                nachname=nachname,
                email=email,
                session=session,
            )
            studenten_dto: Final = [
                StudentDTO.from_student(student) for student in studenten
            ]
            session.commit()

        logger.debug("{}", studenten_dto)
        return studenten_dto
