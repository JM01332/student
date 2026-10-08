"""Geschäftslogik für Studierende."""

from typing import Any

from loguru import logger

lazy from student.repository import StudentRepository

__all__ = ["StudentService"]


class StudentService:
    """Service-Klasse mit Geschäftslogik für Studierende."""

    def __init__(self, repo: StudentRepository) -> None:
        """Konstruktor mit abhängigem StudentRepository."""
        self.repo: StudentRepository = repo

    def find_by_id(self, student_id: int) -> dict[str, Any] | None:
        """Einen Studierenden anhand der ID suchen.

        :param student_id: ID des gesuchten Studierenden
        :return: Daten des Studierenden oder None, falls es die ID nicht gibt
        """
        logger.debug("student_id={}", student_id)
        return self.repo.find_by_id(student_id)

    def find(self, nachname: str | None, email: str | None) -> list[dict[str, Any]]:
        """Studierende mit optionalen Suchparametern suchen.

        :param nachname: Teil des Nachnamens
        :param email: Emailadresse
        :return: Liste der gefundenen Studierenden, ggf. leer
        """
        logger.debug("nachname={}, email={}", nachname, email)
        return self.repo.find(nachname=nachname, email=email)
