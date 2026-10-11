"""Entity-Klassen für das OR-Mapping mit SQLAlchemy."""

from student.entity.adresse import Adresse
from student.entity.base import Base
from student.entity.pruefungsleistung import Pruefungsleistung
from student.entity.student import Student

__all__ = ["Adresse", "Base", "Pruefungsleistung", "Student"]
