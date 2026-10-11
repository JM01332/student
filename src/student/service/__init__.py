"""Geschäftslogik der Student-Anwendung."""

from student.service.adresse_dto import AdresseDTO
from student.service.pruefungsleistung_dto import PruefungsleistungDTO
from student.service.student_dto import StudentDTO
from student.service.student_service import StudentService

__all__ = ["AdresseDTO", "PruefungsleistungDTO", "StudentDTO", "StudentService"]
