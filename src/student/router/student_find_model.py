"""Pydantic-Modelle für das Lesen von Studierendendaten."""

lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict

lazy from student.service import StudentDTO

__all__ = [
    "AdresseResponseModel",
    "PruefungsleistungResponseModel",
    "StudentResponseModel",
]


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
