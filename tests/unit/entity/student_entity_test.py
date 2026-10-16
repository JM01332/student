"""Unit-Tests für die Entity-Klasse Student."""

from student.entity import Student

ID = 1000
VERSION = 3
USERNAME = "admin"


def test_set_uebernimmt_einfache_attribute() -> None:
    """set() überschreibt nur die Felder aus dem Update-Model."""
    student = Student(
        matrikelnummer="100000",
        nachname="Alt",
        vorname="Alice",
        username=USERNAME,
        id=ID,
        email="alt@h-ka.de",
        adresse=None,
        pruefungsleistungen=[],
        erzeugt=None,
        aktualisiert=None,
        version=VERSION,
    )
    neu = Student(
        matrikelnummer="200000",
        nachname="Neu",
        vorname="Bob",
        username=None,
        id=None,
        email="neu@h-ka.de",
        adresse=None,
        pruefungsleistungen=[],
        erzeugt=None,
        aktualisiert=None,
    )

    student.set(neu)

    assert student.matrikelnummer == neu.matrikelnummer
    assert student.nachname == neu.nachname
    assert student.vorname == neu.vorname
    assert student.email == neu.email
    # unverändert: ID, Version und Benutzername
    assert student.id == ID
    assert student.version == VERSION
    assert student.username == USERNAME
