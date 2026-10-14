"""Pydantic-Model für die Adresse."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from student.entity import Adresse

__all__ = ["AdresseModel"]


class AdresseModel(BaseModel):
    """Pydantic-Model für die Adresse."""

    plz: Annotated[str, StringConstraints(pattern=r"^\d{5}$")]
    """Postleitzahl mit genau 5 Ziffern."""
    ort: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    """Ort."""

    model_config = ConfigDict(
        # Beispiel für die OpenAPI-Beschreibung
        json_schema_extra={
            "example": {
                "plz": "76133",
                "ort": "Karlsruhe",
            },
        },
        # keine automatischen Typumwandlungen, z.B. Zahl statt String
        strict=True,
        # unbekannte Felder im JSON sind ein Fehler
        extra="forbid",
        # das Model ist nach der Validierung unveränderlich
        frozen=True,
    )

    def to_adresse(self) -> Adresse:
        """Konvertierung in ein Adresse-Objekt für SQLAlchemy.

        :return: Adresse-Objekt für SQLAlchemy
        :rtype: Adresse
        """
        return Adresse(
            id=None,
            plz=self.plz,
            ort=self.ort,
            student_id=None,
            student=None,
        )
