"""Entity-Klasse für die Adresse."""

from typing import override

from sqlalchemy import ForeignKey, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student.entity.base import Base
from student.entity.student import Student

__all__ = ["Adresse"]


class Adresse(Base):
    """Entity-Klasse für die Adresse."""

    __tablename__ = "adresse"

    plz: Mapped[str]
    """Die 5-stellige Postleitzahl."""

    ort: Mapped[str]
    """Der Ort."""

    id: Mapped[int | None] = mapped_column(
        Identity(start=1000),
        primary_key=True,
    )
    """Die generierte ID gemäß der zugehörigen IDENTITY-Spalte."""

    student_id: Mapped[int | None] = mapped_column(ForeignKey("student.id"))
    """ID des zugehörigen Studierenden als Fremdschlüssel in der DB-Tabelle."""

    student: Mapped[Student | None] = relationship(back_populates=Student.adresse)
    """Das zugehörige transiente Student-Objekt."""

    @override
    def __repr__(self) -> str:
        """Ausgabe einer Adresse als String ohne die Studierendendaten."""
        return f"Adresse(id={self.id}, plz={self.plz}, ort={self.ort})"
