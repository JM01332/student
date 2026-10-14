"""Unit-Tests für die Umwandlung von StudentDTO in StudentResponseModel."""

from decimal import Decimal

from student.router.student_find_model import StudentResponseModel
from student.service import AdresseDTO, PruefungsleistungDTO, StudentDTO


def _student_dto() -> StudentDTO:
    """StudentDTO mit Adresse und einer Prüfungsleistung als Testdaten."""
    return StudentDTO(
        id=1,
        version=3,
        matrikelnummer="123456",
        nachname="Mocktest",
        vorname="Max",
        email="mock@h-ka.de",
        username="mocktest",
        adresse=AdresseDTO(plz="11111", ort="Mockort"),
        pruefungsleistungen=[
            PruefungsleistungDTO(
                modul="Softwareengineering",
                note=Decimal("1.3"),
                semester="WS 2026/27",
            ),
        ],
    )


def test_from_dto_uebernimmt_attribute() -> None:
    """Alle Attribute einschließlich Adresse und Prüfungsleistungen werden kopiert."""
    model = StudentResponseModel.from_dto(_student_dto())

    assert model.nachname == "Mocktest"
    assert model.adresse is not None
    assert model.adresse.ort == "Mockort"
    assert [p.note for p in model.pruefungsleistungen] == [Decimal("1.3")]


def test_from_dto_ohne_version() -> None:
    """Die Versionsnummer ist nicht im JSON, sie kommt bei GET nach ID als ETag."""
    json = StudentResponseModel.from_dto(_student_dto()).model_dump(mode="json")

    assert "version" not in json
    assert json["pruefungsleistungen"][0]["note"] == "1.3"
