"""HTTP-Tests für das Lesen von Studierenden gegen den laufenden Server."""

from http import HTTPStatus

import pytest
lazy from httpx import Client


def test_get_by_id(client: Client) -> None:
    """Ein vorhandener Studierender wird mit HTTP 200 und seinen Daten geliefert."""
    response = client.get("/rest/1")

    assert response.status_code == HTTPStatus.OK
    assert response.json()["nachname"] == "Mustermann"
    assert response.headers["etag"] == '"0"'
    assert "version" not in response.json()
    assert response.json()["pruefungsleistungen"][0]["note"] == "1.3"


def test_get_by_id_not_modified(client: Client) -> None:
    """Eine passende Version liefert 304 ohne Body und mit aktuellem ETag."""
    response = client.get("/rest/1", headers={"If-None-Match": '"0"'})

    assert response.status_code == HTTPStatus.NOT_MODIFIED
    assert response.content == b""
    assert response.headers["etag"] == '"0"'


@pytest.mark.parametrize("etag", ['"99"', '"abc"', "0", '""'])
def test_get_by_id_other_or_invalid_etag(client: Client, etag: str) -> None:
    """Andere oder ungültige Versionen liefern weiterhin den Datensatz."""
    response = client.get("/rest/1", headers={"If-None-Match": etag})

    assert response.status_code == HTTPStatus.OK
    assert response.headers["etag"] == '"0"'
    assert response.json()["id"] == 1


# Derselbe Test läuft einmal pro Wert: 0 als Grenzfall, 999999 als hohe ID
@pytest.mark.parametrize("student_id", [0, 999999])
def test_get_by_id_not_found(client: Client, student_id: int) -> None:
    """Für eine nicht vorhandene ID wird HTTP 404 mit ProblemDetails geliefert."""
    response = client.get(f"/rest/{student_id}")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Not Found"


def test_get_ohne_suchparameter(client: Client) -> None:
    """Ohne Suchparameter werden alle Studierenden geliefert."""
    response = client.get("/rest")

    assert response.status_code == HTTPStatus.OK
    assert {student["id"] for student in response.json()} == {1, 20, 30, 40, 50}


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
    """Für einen nicht vorhandenen Nachnamen wird 404 mit ProblemDetails geliefert."""
    response = client.get("/rest", params={"nachname": "xyz"})

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["title"] == "Not Found"


@pytest.mark.parametrize(
    ("nachname", "expected_status"),
    [("muster", HTTPStatus.OK), ("Mustermann", HTTPStatus.NOT_FOUND)],
)
def test_get_kombinierte_suchparameter(
    client: Client, nachname: str, expected_status: HTTPStatus
) -> None:
    """Bei kombinierten Filtern müssen Nachname und Emailadresse passen."""
    response = client.get(
        "/rest",
        params={"nachname": nachname, "email": "erika.musterfrau@h-ka.de"},
    )

    assert response.status_code == expected_status
    if expected_status == HTTPStatus.OK:
        assert [student["vorname"] for student in response.json()] == ["Erika"]


def test_get_unbekannter_suchparameter(client: Client) -> None:
    """Unbekannte Parameter werden auch neben einem gültigen Filter abgewiesen."""
    response = client.get("/rest", params={"nachname": "muster", "nachnam": "muster"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    error = response.json()["detail"][0]
    assert error["type"] == "extra_forbidden"
    assert error["loc"] == ["query", "nachnam"]
