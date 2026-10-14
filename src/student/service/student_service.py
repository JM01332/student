"""Geschäftslogik für Studierende."""

from typing import Final

from loguru import logger

from student.repository import Session
from student.service.exceptions import NotFoundError
from student.service.student_dto import StudentDTO
lazy from student.repository import StudentRepository
lazy from student.repository.pageable import Pageable

__all__ = ["StudentService"]


class StudentService:
    """Service-Klasse mit Geschäftslogik für Studierende."""

    def __init__(self, repo: StudentRepository) -> None:
        """Konstruktor mit abhängigem StudentRepository."""
        self.repo: StudentRepository = repo

    def find_by_id(self, student_id: int) -> StudentDTO:
        """Einen Studierenden anhand der ID suchen.

        :param student_id: ID des gesuchten Studierenden
        :return: Daten des gefundenen Studierenden
        :rtype: StudentDTO
        :raises NotFoundError: Falls es keinen Studierenden mit der ID gibt
        """
        logger.debug("student_id={}", student_id)
        # "with" schließt die Session am Ende des Blocks, auch bei einem Fehler
        with Session() as session:
            student: Final = self.repo.find_by_id(
                student_id=student_id,
                session=session,
            )
            if student is None:
                logger.debug("NotFoundError: student_id={}", student_id)
                raise NotFoundError(student_id=student_id)
            # DTO erzeugen, solange die Session noch offen ist
            student_dto: Final = StudentDTO.from_student(student)
            session.commit()

        logger.debug("{}", student_dto)
        return student_dto

    def find(
        self,
        nachname: str | None,
        email: str | None,
        pageable: Pageable | None = None,
    ) -> list[StudentDTO]:
        """Studierende mit optionalen Suchparametern suchen.

        :param nachname: Teil des Nachnamens
        :param email: Emailadresse
        :param pageable: Validierte Seiteneinteilung; None oder size=0 für alle Treffer
        :return: Liste der gefundenen Studierenden
        :rtype: list[StudentDTO]
        :raises NotFoundError: Falls keine Studierenden gefunden wurden
        """
        logger.debug("nachname={}, email={}, pageable={}", nachname, email, pageable)
        with Session() as session:
            studenten: Final = self.repo.find(
                nachname=nachname,
                email=email,
                pageable=pageable,
                session=session,
            )
            if not studenten:
                logger.debug("NotFoundError: nachname={}, email={}", nachname, email)
                raise NotFoundError(nachname=nachname, email=email)
            studenten_dto: Final = [
                StudentDTO.from_student(student) for student in studenten
            ]
            session.commit()

        logger.debug("{}", studenten_dto)
        return studenten_dto

    def count(self, nachname: str | None, email: str | None) -> int:
        """Alle Treffer mit optionalen Suchparametern zählen.

        :param nachname: Teil des Nachnamens
        :param email: Emailadresse
        :return: Gesamtanzahl der passenden Studierenden, ggf. 0
        :rtype: int
        """
        logger.debug("nachname={}, email={}", nachname, email)
        with Session() as session:
            count: Final = self.repo.count(
                nachname=nachname,
                email=email,
                session=session,
            )
            session.commit()

        logger.debug("count={}", count)
        return count
