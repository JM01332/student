"""GraphQL-Mutationen gegen den laufenden Server und den echten Keycloak.

Angelehnt an `tests/integration/graphql_api/mutation_test.py` im Beispielprojekt.
"""

from http import HTTPStatus
from random import randint
from typing import Any, Final
from uuid import uuid4
lazy from collections.abc import Callable

lazy from httpx import Client

GRAPHQL_PATH: Final = "/graphql"
PASSWORD: Final = "p"  # ruff: ignore[hardcoded-password-string]
TOKEN_LAUFZEIT: Final = 1800


def _mutation(
    client: Client, query: str, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    """Mutation per POST senden und den JSON-Body bei Status 200 liefern."""
    response = client.post(GRAPHQL_PATH, json={"query": query}, headers=headers)
    assert response.status_code == HTTPStatus.OK
    return response.json()


def _create(username: str, plz: str = "76133") -> str:
    """create-Mutation mit zufälliger Matrikelnummer und Email."""
    return f"""mutation {{ create(studentInput: {{
      matrikelnummer: "{randint(500000, 999999)}", nachname: "Graph",
      vorname: "Gustav", email: "{username}@h-ka.de", username: "{username}",
      adresse: {{ plz: "{plz}", ort: "Karlsruhe" }},
      pruefungsleistungen: [{{ modul: "Softwareengineering", note: "1.3",
        semester: "WS 2026/27" }}]
    }}) {{ id }} }}"""  # ruff: ignore[suspicious-non-cryptographic-random-usage]


def test_create(client: Client, login: Callable[[str, str], str]) -> None:
    """Anlegen per GraphQL: danach per REST lesbar und als Benutzer einloggbar.

    Der neue Datensatz wird am Ende wieder gelöscht, damit spätere Tests (z.B. die
    Suche und Pagination in student_test.py) weiter genau 5 Studierende finden.
    """
    username = f"gql{uuid4().hex[:8]}"

    body = _mutation(client, _create(username))

    assert "errors" not in body
    neue_id = body["data"]["create"]["id"]
    try:
        gelesen = client.get(f"/rest/{neue_id}")
        assert gelesen.status_code == HTTPStatus.OK
        assert gelesen.json()["username"] == username
        assert login(username, PASSWORD)
    finally:
        client.delete(f"/rest/{neue_id}")


def test_create_ungueltige_daten(client: Client) -> None:
    """Ungültige PLZ: Fehlermeldung aus pydantic unter errors, keine Daten."""
    body = _mutation(client, _create(f"gql{uuid4().hex[:8]}", plz="7"))

    assert body["data"] is None
    assert "adresse.plz" in body["errors"][0]["message"]


def test_create_username_existiert(client: Client) -> None:
    """Ein Benutzername, den es in Keycloak gibt, wird abgelehnt."""
    body = _mutation(client, _create("erika"))

    assert body["data"] is None
    assert "erika" in body["errors"][0]["message"]


def test_create_ohne_admin(
    client_ohne_token: Client, login: Callable[[str, str], str]
) -> None:
    """Als erika (ohne Rolle admin) wird nichts angelegt."""
    headers = {"Authorization": f"Bearer {login('erika', PASSWORD)}"}

    body = _mutation(client_ohne_token, _create(f"gql{uuid4().hex[:8]}"), headers)

    assert body["data"] is None
    assert len(body["errors"]) == 1


def test_login(client_ohne_token: Client) -> None:
    """Login per GraphQL: Token, echte Laufzeit und Rolle ADMIN."""
    body = _mutation(
        client_ohne_token,
        f'mutation {{ login(username: "admin", password: "{PASSWORD}") '
        "{ token expiresIn roles } }",
    )

    login_result = body["data"]["login"]
    assert login_result["token"]
    assert login_result["expiresIn"] == TOKEN_LAUFZEIT
    assert login_result["roles"] == ["ADMIN"]


def test_login_falsches_passwort(client_ohne_token: Client) -> None:
    """Falsches Passwort: Fehler statt Token."""
    body = _mutation(
        client_ohne_token,
        'mutation { login(username: "admin", password: "FALSCH") { token } }',
    )

    assert body["data"] is None
    assert len(body["errors"]) == 1
