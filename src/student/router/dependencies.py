"""Factory-Funktionen für Dependency Injection."""

from student.service import StudentService

__all__ = ["get_service"]


def get_service() -> StudentService:
    """Factory-Funktion für StudentService.

    :return: Der Service
    :rtype: StudentService
    """
    return StudentService()
