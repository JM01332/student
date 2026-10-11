"""DTO-Klasse für Prüfungsleistungen, ohne Abhängigkeit zu SQLAlchemy."""

from dataclasses import dataclass
lazy from decimal import Decimal

lazy from student.entity import Pruefungsleistung

__all__ = ["PruefungsleistungDTO"]


@dataclass(eq=False, slots=True, kw_only=True)
class PruefungsleistungDTO:
    """DTO-Klasse für eine Prüfungsleistung eines Studierenden."""

    modul: str
    note: Decimal
    semester: str

    @classmethod
    def from_pruefungsleistung(
        cls,
        pruefungsleistung: Pruefungsleistung,
    ) -> PruefungsleistungDTO:
        """Initialisierung durch ein Entity-Objekt von Pruefungsleistung.

        :param pruefungsleistung: Pruefungsleistung-Objekt aus SQLAlchemy
        :return: PruefungsleistungDTO-Objekt mit den Daten aus dem Entity-Objekt
        :rtype: PruefungsleistungDTO
        """
        return cls(
            modul=pruefungsleistung.modul,
            note=pruefungsleistung.note,
            semester=pruefungsleistung.semester,
        )
