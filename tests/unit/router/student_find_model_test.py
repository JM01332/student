"""Unit-Tests für Suchparameter und die Umwandlung von StudentDTO."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from student.repository.pageable import Pageable
from student.router.student_find_model import (
    PageMetaModel,
    StudentFindModel,
    StudentPageModel,
    StudentResponseModel,
)
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


def test_find_model_defaults() -> None:
    """Ohne Query-Parameter wird kein Filter gesetzt."""
    model = StudentFindModel()

    assert model.nachname is None
    assert model.email is None
    pageable = model.to_pageable()
    assert pageable.number == 0
    expected_size = 5
    assert pageable.size == expected_size


@pytest.mark.parametrize(
    ("parameter", "value", "error_type"),
    [
        ("page", "-1", "greater_than_equal"),
        ("size", "-1", "greater_than_equal"),
        ("size", "101", "less_than_equal"),
        ("page", "abc", "int_parsing"),
        ("size", "1.5", "int_parsing"),
    ],
)
def test_find_model_rejects_invalid_pagination(
    parameter: str, value: str, error_type: str
) -> None:
    """Ungültige Seitenparameter werden vor dem Service-Aufruf abgewiesen."""
    with pytest.raises(ValidationError) as exc:
        StudentFindModel.model_validate({parameter: value})

    assert exc.value.errors()[0]["loc"] == (parameter,)
    assert exc.value.errors()[0]["type"] == error_type


def test_find_model_rejects_unknown_parameter() -> None:
    """Tippfehler in Suchparametern werden nicht stillschweigend ignoriert."""
    with pytest.raises(ValidationError) as exc:
        StudentFindModel.model_validate({"nachnam": "Muster"})

    assert exc.value.errors()[0]["type"] == "extra_forbidden"
    assert exc.value.errors()[0]["loc"] == ("nachnam",)


def test_find_model_is_frozen() -> None:
    """Ein validierter Suchauftrag ist unveränderlich."""
    model = StudentFindModel(nachname="Muster")

    with pytest.raises(ValidationError) as exc:
        # Absichtlicher Schreibversuch prüft auch den Schutz zur Laufzeit.
        model.nachname = "Anders"  # ty: ignore[invalid-assignment]

    assert exc.value.errors()[0]["type"] == "frozen_instance"


def test_page_model_serialization() -> None:
    """Eine Seite serialisiert Inhalt und Metadaten im vorgesehenen JSON-Format."""
    student = StudentResponseModel.from_dto(_student_dto())
    page = StudentPageModel(
        content=(student,),
        page=PageMetaModel(size=2, number=1, total_elements=3, total_pages=2),
    )

    result = page.model_dump(mode="json")

    assert result == {
        "content": [student.model_dump(mode="json")],
        "page": {"size": 2, "number": 1, "total_elements": 3, "total_pages": 2},
    }
    assert "version" not in result["content"][0]
    assert result["content"][0]["pruefungsleistungen"][0]["note"] == "1.3"


def test_page_model_empty_content() -> None:
    """Das Antwortmodell kann auch eine leere Seite darstellen."""
    page = StudentPageModel(
        content=(),
        page=PageMetaModel(size=5, number=0, total_elements=0, total_pages=0),
    )

    assert page.model_dump(mode="json") == {
        "content": [],
        "page": {"size": 5, "number": 0, "total_elements": 0, "total_pages": 0},
    }


def test_page_model_requires_complete_metadata() -> None:
    """Unvollständige Metadaten dürfen nicht als Seitenantwort ausgegeben werden."""
    with pytest.raises(ValidationError) as exc:
        StudentPageModel.model_validate({"content": [], "page": {"size": 5}})

    assert {error["loc"] for error in exc.value.errors()} == {
        ("page", "number"),
        ("page", "total_elements"),
        ("page", "total_pages"),
    }


@pytest.mark.parametrize(
    ("size", "number", "total_elements", "total_pages"),
    [
        (5, 0, 0, 0),
        (5, 0, 1, 1),
        (5, 0, 5, 1),
        (5, 1, 6, 2),
        (5, 1, 10, 2),
        (5, 2, 11, 3),
        (5, 10, 6, 2),
        (1, 0, 3, 3),
        (0, 0, 5, 1),
        (0, 7, 5, 1),
        (0, 0, 0, 1),
    ],
)
def test_page_metadata_calculation(
    size: int, number: int, total_elements: int, total_pages: int
) -> None:
    """Seitengrenzen und unbegrenzte Abfragen entsprechen dem Beispiel."""
    metadata = PageMetaModel.from_pageable(
        Pageable(size=size, number=number), total_elements
    )

    assert metadata.model_dump() == {
        "size": size,
        "number": number,
        "total_elements": total_elements,
        "total_pages": total_pages,
    }
