"""Unit-Tests für die Validierung der Request-Models beim Anlegen von Studierenden."""

import json
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from student.router.student_model import StudentModel


def _gueltig() -> dict[str, Any]:
    """Gültiger JSON-Datensatz für einen neuen Studierenden."""
    return {
        "matrikelnummer": "999999",
        "nachname": "Müller-Lüdenscheidt",
        "vorname": "Theo",
        "email": "theo.test@h-ka.de",
        "username": "theo",
        "adresse": {"plz": "76133", "ort": "Karlsruhe"},
        "pruefungsleistungen": [
            {"modul": "Softwareengineering", "note": 1.3, "semester": "WS 2026/27"},
            {"modul": "Datenbanken", "note": "2.0", "semester": "SS 2026"},
        ],
    }


def _validieren(daten: dict[str, Any]) -> StudentModel:
    """Validierung wie bei einem HTTP-Request: aus JSON-Text."""
    return StudentModel.model_validate_json(json.dumps(daten))


def test_gueltiger_student() -> None:
    """Ein gültiger Datensatz wird mit Doppelnamen und Noten als Decimal akzeptiert."""
    model = _validieren(_gueltig())

    assert model.nachname == "Müller-Lüdenscheidt"
    assert [p.note for p in model.pruefungsleistungen] == [
        Decimal("1.3"),
        Decimal("2.0"),
    ]


def test_to_student() -> None:
    """Die Konvertierung erzeugt eine Entity mit Adresse und Prüfungsleistungen."""
    student = _validieren(_gueltig()).to_student()

    assert student.id is None
    assert student.username == "theo"
    assert student.adresse is not None
    assert student.adresse.plz == "76133"
    assert [p.modul for p in student.pruefungsleistungen] == [
        "Softwareengineering",
        "Datenbanken",
    ]


def test_ohne_pruefungsleistungen() -> None:
    """Eine leere Liste von Prüfungsleistungen ist erlaubt."""
    daten = _gueltig() | {"pruefungsleistungen": []}

    assert _validieren(daten).pruefungsleistungen == []


@pytest.mark.parametrize(
    ("feld", "wert"),
    [
        ("matrikelnummer", "12345"),
        ("matrikelnummer", "12345a"),
        ("matrikelnummer", 123456),
        ("nachname", "mustermann"),
        ("nachname", "Müller-"),
        ("vorname", ""),
        ("email", "keine-email"),
        ("username", ""),
        ("username", "x" * 21),
    ],
)
def test_ungueltiges_attribut(feld: str, wert: Any) -> None:
    """Ungültige einfache Attribute werden mit dem Feldnamen abgewiesen."""
    daten = _gueltig() | {feld: wert}

    with pytest.raises(ValidationError) as err:
        _validieren(daten)

    assert err.value.errors()[0]["loc"] == (feld,)


@pytest.mark.parametrize(
    ("adresse", "feld"),
    [
        ({"plz": "7613", "ort": "Karlsruhe"}, "plz"),
        ({"plz": "76133", "ort": ""}, "ort"),
    ],
)
def test_ungueltige_adresse(adresse: dict[str, str], feld: str) -> None:
    """Ungültige Adressen werden mit dem Pfad zum Feld abgewiesen."""
    daten = _gueltig() | {"adresse": adresse}

    with pytest.raises(ValidationError) as err:
        _validieren(daten)

    assert err.value.errors()[0]["loc"] == ("adresse", feld)


@pytest.mark.parametrize(
    ("pruefungsleistung", "feld"),
    [
        ({"modul": "SWE", "note": 1.5, "semester": "SS 2026"}, "note"),
        ({"modul": "SWE", "note": 6.0, "semester": "SS 2026"}, "note"),
        ({"modul": "SWE", "note": 1.3, "semester": "WS2026"}, "semester"),
        ({"modul": "", "note": 1.3, "semester": "SS 2026"}, "modul"),
    ],
)
def test_ungueltige_pruefungsleistung(
    pruefungsleistung: dict[str, Any],
    feld: str,
) -> None:
    """Unzulässige Noten und falsche Semesterangaben werden abgewiesen."""
    daten = _gueltig() | {"pruefungsleistungen": [pruefungsleistung]}

    with pytest.raises(ValidationError) as err:
        _validieren(daten)

    assert err.value.errors()[0]["loc"] == ("pruefungsleistungen", 0, feld)


def test_unbekanntes_feld() -> None:
    """Unbekannte Felder, z.B. eine mitgeschickte ID, sind nicht erlaubt."""
    daten = _gueltig() | {"id": 1}

    with pytest.raises(ValidationError) as err:
        _validieren(daten)

    assert err.value.errors()[0]["type"] == "extra_forbidden"


def test_fehlende_adresse() -> None:
    """Die Adresse ist Pflicht."""
    daten = _gueltig()
    del daten["adresse"]

    with pytest.raises(ValidationError) as err:
        _validieren(daten)

    assert err.value.errors()[0]["type"] == "missing"
