"""Entity-Klasse für Studierendendaten."""

from typing import override
lazy from datetime import datetime

from sqlalchemy import Identity, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from student.entity.base import Base
lazy from student.entity.adresse import Adresse
lazy from student.entity.pruefungsleistung import Pruefungsleistung

__all__ = ["Student"]


class Student(Base):
    """Entity-Klasse für Studierendendaten."""

    __tablename__ = "student"

    matrikelnummer: Mapped[str]
    """Die eindeutige 6-stellige Matrikelnummer."""

    nachname: Mapped[str]
    """Der Nachname."""

    vorname: Mapped[str]
    """Der Vorname."""

    username: Mapped[str | None]
    """Der Benutzername für Login."""

    id: Mapped[int | None] = mapped_column(
        Identity(start=1000),
        primary_key=True,
    )
    """Die generierte ID gemäß der zugehörigen IDENTITY-Spalte."""

    email: Mapped[str] = mapped_column(unique=True)
    """Die eindeutige Emailadresse."""

    adresse: Mapped[Adresse | None] = relationship(
        back_populates=lambda: Adresse.student,
        innerjoin=True,
        cascade="save-update, delete",
    )
    """Die in einer 1:1-Beziehung referenzierte Adresse."""

    pruefungsleistungen: Mapped[list[Pruefungsleistung]] = relationship(
        back_populates=lambda: Pruefungsleistung.student,
        cascade="save-update, delete",
    )
    """Die in einer 1:N-Beziehung referenzierten Prüfungsleistungen."""

    erzeugt: Mapped[datetime | None] = mapped_column(
        insert_default=func.now(),
    )
    """Der Zeitstempel für das initiale INSERT in die DB-Tabelle."""

    aktualisiert: Mapped[datetime | None] = mapped_column(
        insert_default=func.now(),
        onupdate=func.now(),
    )
    """Der Zeitstempel vom letzten UPDATE in der DB-Tabelle."""

    version: Mapped[int] = mapped_column(nullable=False, default=0)
    """Die Versionsnummer für optimistische Synchronisation."""

    __mapper_args__ = {"version_id_col": version}  # ruff: ignore[mutable-class-default]

    @override
    def __eq__(self, other: object) -> bool:
        """Vergleich auf Gleichheit anhand der ID, ohne Joins zu verursachen."""
        if self is other:
            return True
        if not isinstance(other, type(self)):
            return False
        return self.id is not None and self.id == other.id

    def __hash__(self) -> int:
        """Hash-Funktion anhand der ID, ohne Joins zu verursachen."""
        return hash(self.id) if self.id is not None else hash(type(self))

    @override
    def __repr__(self) -> str:
        """Ausgabe eines Studierenden als String, ohne Joins zu verursachen."""
        return (
            f"Student(id={self.id}, version={self.version}, "
            f"matrikelnummer={self.matrikelnummer}, nachname={self.nachname}, "
            f"vorname={self.vorname}, email={self.email}, username={self.username}, "
            f"erzeugt={self.erzeugt}, aktualisiert={self.aktualisiert})"
        )
