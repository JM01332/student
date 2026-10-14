"""Pydantic-Model für das Anlegen von Studierenden."""

from typing import Annotated, Final, override

from loguru import logger
from pydantic import ConfigDict, StringConstraints

from student.router.student_update_model import StudentUpdateModel
lazy from student.entity import Student
lazy from student.router.adresse_model import AdresseModel
lazy from student.router.pruefungsleistung_model import PruefungsleistungModel

__all__ = ["StudentModel"]


class StudentModel(StudentUpdateModel):
    """Pydantic-Model für neue Studierende mit Adresse und Prüfungsleistungen."""

    username: Annotated[str, StringConstraints(min_length=1, max_length=20)]
    """Der Benutzername für Login."""
    adresse: AdresseModel
    """Die zugehörige Adresse (1:1)."""
    pruefungsleistungen: list[PruefungsleistungModel]
    """Die Prüfungsleistungen (1:N), ggf. eine leere Liste."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "matrikelnummer": "999999",
                "nachname": "Test",
                "vorname": "Theo",
                "email": "theo.test@h-ka.de",
                "username": "theo",
                "adresse": {"plz": "76133", "ort": "Karlsruhe"},
                "pruefungsleistungen": [
                    {
                        "modul": "Softwareengineering",
                        "note": "1.3",
                        "semester": "WS 2026/27",
                    },
                ],
            },
        },
        strict=True,
        extra="forbid",
        frozen=True,
    )

    @override
    def to_student(self) -> Student:
        """Konvertierung in ein Student-Objekt für SQLAlchemy.

        :return: Student-Objekt mit Benutzername, Adresse und Prüfungsleistungen
        :rtype: Student
        """
        student: Final = super().to_student()
        student.username = self.username
        student.adresse = self.adresse.to_adresse()
        student.pruefungsleistungen = [
            pruefungsleistung.to_pruefungsleistung()
            for pruefungsleistung in self.pruefungsleistungen
        ]
        logger.debug("student={}", student)
        return student
