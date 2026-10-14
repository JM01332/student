"""DTO-Klasse für Studierendendaten, ohne Abhängigkeit zu SQLAlchemy."""

from dataclasses import dataclass

from student.service.adresse_dto import AdresseDTO
from student.service.pruefungsleistung_dto import PruefungsleistungDTO
lazy from student.entity import Student

__all__ = ["StudentDTO"]


@dataclass(eq=False, slots=True, kw_only=True)
class StudentDTO:
    """DTO-Klasse für gelesene Studierendendaten.

    Die Daten werden aus dem Entity-Objekt kopiert, solange die Session offen ist.
    Danach ist das DTO unabhängig von SQLAlchemy und hat keine Rückwärtsverweise.
    """

    id: int
    version: int
    matrikelnummer: str
    nachname: str
    vorname: str
    email: str
    username: str
    adresse: AdresseDTO | None
    pruefungsleistungen: list[PruefungsleistungDTO]

    @classmethod
    def from_student(cls, student: Student) -> StudentDTO:
        """Initialisierung von StudentDTO durch ein Entity-Objekt von Student.

        :param student: Student-Objekt aus SQLAlchemy mit geladenen Beziehungen
        :return: StudentDTO-Objekt mit den Daten aus dem Student-Objekt
        :rtype: StudentDTO
        """
        return cls(
            id=student.id if student.id is not None else -1,
            version=student.version,
            matrikelnummer=student.matrikelnummer,
            nachname=student.nachname,
            vorname=student.vorname,
            email=student.email,
            username=student.username if student.username is not None else "N/A",
            adresse=(
                AdresseDTO.from_adresse(student.adresse)
                if student.adresse is not None
                else None
            ),
            pruefungsleistungen=[
                PruefungsleistungDTO.from_pruefungsleistung(pruefungsleistung)
                for pruefungsleistung in student.pruefungsleistungen
            ],
        )
