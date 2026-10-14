"""Pydantic-Model für Prüfungsleistungen."""

from decimal import Decimal
from typing import Annotated, Final

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from student.entity import Pruefungsleistung

__all__ = ["ZULAESSIGE_NOTEN", "PruefungsleistungModel"]

ZULAESSIGE_NOTEN: Final = frozenset(
    Decimal(note)
    for note in (
        "1.0",
        "1.3",
        "1.7",
        "2.0",
        "2.3",
        "2.7",
        "3.0",
        "3.3",
        "3.7",
        "4.0",
        "5.0",
    )
)
"""Zulässige Notenstufen, wie im CHECK-Constraint der Tabelle pruefungsleistung."""


class PruefungsleistungModel(BaseModel):
    """Pydantic-Model für eine Prüfungsleistung."""

    modul: Annotated[str, StringConstraints(min_length=1, max_length=64)]
    """Das Modul, z.B. Softwareengineering."""
    note: Decimal = Field(strict=False)
    """Die Note. Keine strikte Validierung: JSON liefert eine Zahl oder einen String."""
    semester: Annotated[str, StringConstraints(pattern=r"^(WS \d{4}/\d{2}|SS \d{4})$")]
    """Das Semester, z.B. 'WS 2026/27' oder 'SS 2026'."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "modul": "Softwareengineering",
                "note": "1.3",
                "semester": "WS 2026/27",
            },
        },
        strict=True,
        extra="forbid",
        frozen=True,
    )

    @field_validator("note")
    @classmethod
    def note_zulaessig(cls, note: Decimal) -> Decimal:
        """Nur die zulässigen Notenstufen akzeptieren.

        :param note: Bereits in Decimal umgewandelte Note
        :return: Die unveränderte Note
        :rtype: Decimal
        :raises ValueError: Falls die Note keine zulässige Notenstufe ist
        """
        if note not in ZULAESSIGE_NOTEN:
            msg = "keine zulässige Notenstufe"
            raise ValueError(msg)
        return note

    def to_pruefungsleistung(self) -> Pruefungsleistung:
        """Konvertierung in ein Pruefungsleistung-Objekt für SQLAlchemy.

        :return: Pruefungsleistung-Objekt für SQLAlchemy
        :rtype: Pruefungsleistung
        """
        return Pruefungsleistung(
            id=None,
            modul=self.modul,
            note=self.note,
            semester=self.semester,
            student_id=None,
            student=None,
        )
