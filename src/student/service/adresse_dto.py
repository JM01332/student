"""DTO-Klasse für die Adresse, ohne Abhängigkeit zu SQLAlchemy."""

from dataclasses import dataclass

lazy from student.entity import Adresse

__all__ = ["AdresseDTO"]


@dataclass(eq=False, slots=True, kw_only=True)
class AdresseDTO:
    """DTO-Klasse für die Adresse eines Studierenden."""

    plz: str
    ort: str

    @classmethod
    def from_adresse(cls, adresse: Adresse) -> AdresseDTO:
        """Initialisierung von AdresseDTO durch ein Entity-Objekt von Adresse.

        :param adresse: Adresse-Objekt aus SQLAlchemy
        :return: AdresseDTO-Objekt mit den Daten aus dem Adresse-Objekt
        :rtype: AdresseDTO
        """
        return cls(plz=adresse.plz, ort=adresse.ort)
