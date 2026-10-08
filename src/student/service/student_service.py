"""Geschäftslogik für Studierende."""

from typing import Any, Final

__all__ = ["StudentService"]

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


class StudentService:
    """Service-Klasse mit Geschäftslogik für Studierende."""

    def find_by_id(self, student_id: int) -> dict[str, Any] | None:
        """Einen Studierenden anhand der ID suchen.

        :param student_id: ID des gesuchten Studierenden
        :return: Daten des Studierenden oder None, falls es die ID nicht gibt
        """
        return _STUDENTEN.get(student_id)
