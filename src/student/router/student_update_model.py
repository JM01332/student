"""Pydantic-Model zum Aktualisieren von Studierendendaten."""

from typing import Annotated, Final

from loguru import logger
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

from student.entity import Student

__all__ = ["NAME_PATTERN", "StudentUpdateModel"]

NAME_PATTERN: Final = r"^[A-ZÄÖÜ][a-zäöüß]+(-[A-ZÄÖÜ][a-zäöüß]+)?$"
"""Name mit großem Anfangsbuchstaben, optional als Doppelname mit Bindestrich.

Im Beispielprojekt fehlt im zweiten Teil das `+`, sodass dort nach dem Bindestrich
nur ein einzelner Kleinbuchstabe erlaubt ist (z.B. „Müller-L“, aber nicht
„Müller-Lüdenscheidt“).
"""


class StudentUpdateModel(BaseModel):
    """Pydantic-Model zum Aktualisieren von Studierendendaten.

    Enthält wie im Beispielprojekt alle einfachen Attribute. Benutzername, Adresse und
    Prüfungsleistungen gibt es nur beim Anlegen (`StudentModel`).
    """

    matrikelnummer: Annotated[str, StringConstraints(pattern=r"^\d{6}$")]
    """Die eindeutige Matrikelnummer mit genau 6 Ziffern."""
    nachname: Annotated[str, StringConstraints(pattern=NAME_PATTERN, max_length=64)]
    """Der Nachname."""
    vorname: Annotated[str, StringConstraints(pattern=NAME_PATTERN, max_length=64)]
    """Der Vorname."""
    email: EmailStr
    """Die eindeutige Emailadresse."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matrikelnummer": "999999",
                "nachname": "Test",
                "vorname": "Theo",
                "email": "theo.test@h-ka.de",
            },
        },
        strict=True,
        extra="forbid",
        frozen=True,
    )

    def to_student(self) -> Student:
        """Konvertierung in ein Student-Objekt für SQLAlchemy.

        :return: Student-Objekt ohne Benutzername, Adresse und Prüfungsleistungen
        :rtype: Student
        """
        logger.debug("self={}", self)
        student: Final = Student(
            id=None,
            matrikelnummer=self.matrikelnummer,
            nachname=self.nachname,
            vorname=self.vorname,
            email=self.email,
            username=None,
            adresse=None,
            pruefungsleistungen=[],
            erzeugt=None,
            aktualisiert=None,
        )
        logger.debug("student={}", student)
        return student
