"""Factory-Funktionen für Dependency Injection."""

from typing import Annotated

from fastapi import Depends

from student.repository import StudentRepository
from student.service import StudentService, StudentWriteService

__all__ = ["get_repository", "get_service", "get_write_service"]


def get_repository() -> StudentRepository:
    """Factory-Funktion für StudentRepository.

    :return: Das Repository
    :rtype: StudentRepository
    """
    return StudentRepository()


def get_service(
    repo: Annotated[StudentRepository, Depends(get_repository)],
) -> StudentService:
    """Factory-Funktion für StudentService.

    :param repo: Injiziertes Repository
    :return: Der Service
    :rtype: StudentService
    """
    return StudentService(repo=repo)


def get_write_service(
    repo: Annotated[StudentRepository, Depends(get_repository)],
) -> StudentWriteService:
    """Factory-Funktion für StudentWriteService.

    :param repo: Injiziertes Repository
    :return: Der Service zum Schreiben
    :rtype: StudentWriteService
    """
    return StudentWriteService(repo=repo)
