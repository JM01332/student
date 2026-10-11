"""Repository für den Datenzugriff auf Studierende."""

from typing import Any, Final

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
lazy from sqlalchemy.orm import Session

from student.entity import Student

__all__ = ["StudentRepository"]

# Beispieldaten im Speicher, bis die Datenbank angebunden ist
_STUDENTEN: Final[dict[int, dict[str, Any]]] = {
    1: {
        "id": 1,
        "matrikelnummer": "123456",
        "nachname": "Mustermann",
        "vorname": "Max",
        "email": "max.mustermann@h-ka.de",
        "adresse": {"plz": "76133", "ort": "Karlsruhe"},
        "pruefungsleistungen": [
            {"modul": "Softwareengineering", "note": 1.3, "semester": "WS 2026/27"},
        ],
    },
    2: {
        "id": 2,
        "matrikelnummer": "654321",
        "nachname": "Musterfrau",
        "vorname": "Erika",
        "email": "erika.musterfrau@h-ka.de",
        "adresse": {"plz": "76131", "ort": "Karlsruhe"},
        "pruefungsleistungen": [],
    },
}


class StudentRepository:
    """Repository-Klasse mit Lesezugriff auf Studierende."""

    def find_by_id(self, student_id: int, session: Session) -> Student | None:
        """Suche mit der Student-ID in der DB.

        Die Adresse wird per JOIN mitgeladen (1:1), die Prüfungsleistungen mit
        einer zweiten Abfrage per `IN` (1:N), damit kein N+1-Problem entsteht.

        :param student_id: ID des gesuchten Studierenden
        :param session: Session für SQLAlchemy
        :return: Der gefundene Studierende oder None
        :rtype: Student | None
        """
        logger.debug("student_id={}", student_id)
        statement: Final = (
            select(Student)
            .options(
                joinedload(Student.adresse),
                selectinload(Student.pruefungsleistungen),
            )
            .where(Student.id == student_id)
        )
        student: Final = session.scalar(statement)
        logger.debug("{}", student)
        return student

    def find(self, nachname: str | None, email: str | None) -> list[dict[str, Any]]:
        """Suche mit optionalen Suchparametern.

        :param nachname: Teil des Nachnamens, ohne Groß-/Kleinschreibung
        :param email: Emailadresse, ohne Groß-/Kleinschreibung
        :return: Liste der gefundenen Studierenden, ggf. leer
        """
        logger.debug("nachname={}, email={}", nachname, email)
        studenten = list(_STUDENTEN.values())
        if nachname is not None:
            studenten = [
                s for s in studenten if nachname.lower() in s["nachname"].lower()
            ]
        if email is not None:
            studenten = [s for s in studenten if s["email"].lower() == email.lower()]
        logger.debug("{}", studenten)
        return studenten
