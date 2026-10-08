"""Repository für den Datenzugriff auf Studierende."""

from typing import Any, Final

from loguru import logger

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

    def find_by_id(self, student_id: int) -> dict[str, Any] | None:
        """Suche mit der Student-ID.

        :param student_id: ID des gesuchten Studierenden
        :return: Daten des Studierenden oder None, falls es die ID nicht gibt
        """
        logger.debug("student_id={}", student_id)
        student: Final = _STUDENTEN.get(student_id)
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
