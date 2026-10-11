"""Datenzugriff der Student-Anwendung."""

from student.repository.session_factory import Session, engine
from student.repository.student_repository import StudentRepository

__all__ = ["Session", "StudentRepository", "engine"]
