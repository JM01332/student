"""Pydantic-Modelle für das Lesen von Studierendendaten."""

from typing import Annotated
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from student.repository.pageable import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    Pageable,
)
lazy from student.service import StudentDTO

__all__ = [
    "AdresseResponseModel",
    "PruefungsleistungResponseModel",
    "StudentFindModel",
    "StudentResponseModel",
]


class StudentFindModel(BaseModel):
    """Suchparameter und Pagination für die Suche nach Studierenden."""

    nachname: str | None = None
    email: str | None = None
    page: Annotated[int, Field(ge=DEFAULT_PAGE_NUMBER)] = DEFAULT_PAGE_NUMBER
    size: Annotated[int, Field(ge=0, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE

    model_config = ConfigDict(extra="forbid", frozen=True)

    def to_pageable(self) -> Pageable:
        """Erzeugt die Pagination-Daten aus den validierten Parametern."""
        return Pageable(number=self.page, size=self.size)


class AdresseResponseModel(BaseModel):
    """Adresse als Teil eines Response-Modells für Studierende.

    Damit beim Konvertieren von `StudentDTO` in `StudentResponseModel` auch die
    Attribute von `AdresseDTO` übernommen werden, ist `from_attributes=True` nötig.
    """

    plz: str
    ort: str

    model_config = ConfigDict(from_attributes=True, strict=True, extra="forbid")


class PruefungsleistungResponseModel(BaseModel):
    """Prüfungsleistung als Teil eines Response-Modells für Studierende."""

    modul: str
    note: Decimal
    semester: str

    model_config = ConfigDict(from_attributes=True, strict=True, extra="forbid")


class StudentResponseModel(BaseModel):
    """Pydantic-Modell für einen gefundenen Studierenden als Response.

    Die Versionsnummer ist bewusst nicht enthalten: Sie wird bei GET nach ID als ETag im
    Header übertragen, wie im FastAPI-Beispiel.
    """

    id: int
    matrikelnummer: str
    nachname: str
    vorname: str
    email: str
    username: str
    adresse: AdresseResponseModel | None
    pruefungsleistungen: list[PruefungsleistungResponseModel]

    model_config = ConfigDict(from_attributes=True, strict=True, extra="forbid")

    @classmethod
    def from_dto(cls, student: StudentDTO) -> StudentResponseModel:
        """Konvertiert ein StudentDTO in ein Pydantic-Modell für einen Response.

        `model_validate` übernimmt dank `from_attributes=True` die gleichnamigen
        Attribute aus dem DTO-Objekt, auch die verschachtelten.

        :param student: DTO aus dem Service
        :return: Pydantic-Modell für den Response
        :rtype: StudentResponseModel
        """
        return cls.model_validate(student)
