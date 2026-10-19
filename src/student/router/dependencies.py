"""Factory-Funktionen für Dependency Injection."""

from typing import Annotated

from fastapi import Depends

from student.repository import StudentRepository
from student.security.dependencies import get_user_service
from student.service import StudentService, StudentWriteService
lazy from student.security import UserService

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
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> StudentWriteService:
    """Factory-Funktion für StudentWriteService.

    :param repo: Injiziertes Repository
    :param user_service: Injizierter Service für Benutzer in Keycloak
    :return: Der Service zum Schreiben
    :rtype: StudentWriteService
    """
    return StudentWriteService(repo=repo, user_service=user_service)
