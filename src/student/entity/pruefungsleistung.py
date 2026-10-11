"""Entity-Klasse für Prüfungsleistungen."""

from typing import override
lazy from decimal import Decimal

from sqlalchemy import ForeignKey, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student.entity.base import Base
from student.entity.student import Student

__all__ = ["Pruefungsleistung"]


class Pruefungsleistung(Base):
    """Entity-Klasse für Prüfungsleistungen."""

    __tablename__ = "pruefungsleistung"

    modul: Mapped[str]
    """Das Modul, z.B. Softwareengineering."""

    # Decimal statt float, damit z.B. 1.3 exakt gespeichert wird
    note: Mapped[Decimal]
    """Die Note als zulässige Notenstufe zwischen 1.0 und 5.0."""

    semester: Mapped[str]
    """Das Semester, z.B. WS 2026/27."""

    id: Mapped[int | None] = mapped_column(
        Identity(start=1000),
        primary_key=True,
    )
    """Die generierte ID gemäß der zugehörigen IDENTITY-Spalte."""

    student_id: Mapped[int | None] = mapped_column(ForeignKey("student.id"))
    """ID des zugehörigen Studierenden als Fremdschlüssel in der DB-Tabelle."""

    student: Mapped[Student | None] = relationship(
        back_populates=Student.pruefungsleistungen,
    )
    """Das zugehörige transiente Student-Objekt."""

    @override
    def __repr__(self) -> str:
        """Ausgabe einer Prüfungsleistung als String ohne die Studierendendaten."""
        return (
            f"Pruefungsleistung(id={self.id}, modul={self.modul}, "
            f"note={self.note}, semester={self.semester})"
        )
