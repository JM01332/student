"""Geschäftslogik der Student-Anwendung."""

from student.service.adresse_dto import AdresseDTO
from student.service.exceptions import (
    EmailExistsError,
    MatrikelnummerExistsError,
    NotFoundError,
    VersionOutdatedError,
)
from student.service.pruefungsleistung_dto import PruefungsleistungDTO
from student.service.student_dto import StudentDTO
from student.service.student_service import StudentService
from student.service.student_write_service import StudentWriteService

__all__ = [
    "AdresseDTO",
    "EmailExistsError",
    "MatrikelnummerExistsError",
    "NotFoundError",
    "PruefungsleistungDTO",
    "StudentDTO",
    "StudentService",
    "StudentWriteService",
    "VersionOutdatedError",
]
