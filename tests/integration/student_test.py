"""HTTP-Tests für das Lesen von Studierenden gegen den laufenden Server."""

from http import HTTPStatus

lazy from httpx import Client


def test_get_by_id(client: Client) -> None:
    """Ein vorhandener Studierender wird mit HTTP 200 und seinen Daten geliefert."""
    response = client.get("/rest/1")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["nachname"] == "Mustermann"


def test_get_by_id_not_found(client: Client) -> None:
    """Für eine nicht vorhandene ID wird HTTP 404 geliefert."""
    response = client.get("/rest/999")

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_ohne_suchparameter(client: Client) -> None:
    """Ohne Suchparameter werden alle Studierenden geliefert."""
    response = client.get("/rest")

    assert response.status_code == HTTPStatus.OK
    assert {student["id"] for student in response.json()} == {1, 2}


def test_get_teil_nachname(client: Client) -> None:
    """Die Suche nach einem Teil des Nachnamens liefert alle passenden Treffer."""
    response = client.get("/rest", params={"nachname": "muster"})

    assert response.status_code == HTTPStatus.OK
    nachnamen = {student["nachname"] for student in response.json()}
    assert nachnamen == {"Mustermann", "Musterfrau"}


def test_get_nachname_ohne_gross_kleinschreibung(client: Client) -> None:
    """Die Suche nach dem Nachnamen ignoriert Groß- und Kleinschreibung."""
    response = client.get("/rest", params={"nachname": "MANN"})

    assert response.status_code == HTTPStatus.OK
    assert [student["nachname"] for student in response.json()] == ["Mustermann"]


def test_get_email(client: Client) -> None:
    """Die Suche nach der Emailadresse liefert genau einen Treffer."""
    response = client.get("/rest", params={"email": "erika.musterfrau@h-ka.de"})

    assert response.status_code == HTTPStatus.OK
    assert [student["vorname"] for student in response.json()] == ["Erika"]


def test_get_nicht_vorhandener_nachname(client: Client) -> None:
    """Für einen nicht vorhandenen Nachnamen wird HTTP 404 geliefert."""
    response = client.get("/rest", params={"nachname": "xyz"})

    assert response.status_code == HTTPStatus.NOT_FOUND
