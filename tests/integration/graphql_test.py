"""GraphQL-Queries gegen den laufenden Server und den echten Keycloak.

Angelehnt an `tests/integration/graphql_api/query_test.py` im Beispielprojekt.
GraphQL antwortet auch bei Fehlern mit 200; Fehler stehen im Body unter `errors`.
"""

from http import HTTPStatus
from typing import Any, Final
lazy from collections.abc import Callable

import pytest
lazy from httpx import Client

GRAPHQL_PATH: Final = "/graphql"
PASSWORD: Final = "p"  # ruff: ignore[hardcoded-password-string]


def _query(
    client: Client, query: str, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    """Query per POST senden und den JSON-Body bei Status 200 liefern."""
    response = client.post(GRAPHQL_PATH, json={"query": query}, headers=headers)
    assert response.status_code == HTTPStatus.OK
    return response.json()


def test_student(client: Client) -> None:
    """Als admin: Daten mit Adresse und Prüfungsleistungen wie angefragt."""
    body = _query(
        client,
        '{ student(studentId: "1") { id nachname adresse { ort }'
        " pruefungsleistungen { modul note } } }",
    )

    assert "errors" not in body
    student = body["data"]["student"]
    assert student["nachname"] == "Mustermann"
    assert student["adresse"]["ort"] == "Karlsruhe"
    assert student["pruefungsleistungen"][0]["note"] == "1.3"
    # nur angefragte Felder, z.B. keine Email
    assert "email" not in student


@pytest.mark.parametrize("student_id", [0, 999999])
def test_student_nicht_vorhanden(client: Client, student_id: int) -> None:
    """Unbekannte ID als admin: null ohne Fehler."""
    body = _query(client, f'{{ student(studentId: "{student_id}") {{ nachname }} }}')

    assert body == {"data": {"student": None}}


def test_student_als_erika(
    client_ohne_token: Client, login: Callable[[str, str], str]
) -> None:
    """Studierende sehen ihren eigenen Datensatz, ein fremder ergibt einen Fehler."""
    headers = {"Authorization": f"Bearer {login('erika', PASSWORD)}"}

    eigener = _query(
        client_ohne_token, '{ student(studentId: "20") { username } }', headers
    )
    fremder = _query(
        client_ohne_token, '{ student(studentId: "1") { username } }', headers
    )

    assert eigener == {"data": {"student": {"username": "erika"}}}
    assert fremder["data"] == {"student": None}
    assert len(fremder["errors"]) == 1


def test_student_ohne_token(client_ohne_token: Client) -> None:
    """Ohne Token: Fehler unter errors statt Daten."""
    body = _query(client_ohne_token, '{ student(studentId: "1") { nachname } }')

    assert body["data"] == {"student": None}
    assert len(body["errors"]) == 1


@pytest.mark.parametrize(
    ("suchparameter", "ids"),
    [
        ('{nachname: "muster"}', [1, 20]),
        ('{email: "LENA.SCHMIDT@h-ka.de"}', [30]),
        ("null", [1, 20, 30, 40, 50]),
        ('{nachname: "gibt-es-nicht"}', []),
    ],
)
def test_studenten(client: Client, suchparameter: str, ids: list[int]) -> None:
    """Suche als admin ohne Seiteneinteilung: alle Treffer, ggf. eine leere Liste."""
    body = _query(client, f"{{ studenten(suchparameter: {suchparameter}) {{ id }} }}")

    assert body == {"data": {"studenten": [{"id": i} for i in ids]}}


def test_studenten_als_erika(
    client_ohne_token: Client, login: Callable[[str, str], str]
) -> None:
    """Ohne Rolle admin liefert die Suche eine leere Liste."""
    headers = {"Authorization": f"Bearer {login('erika', PASSWORD)}"}

    body = _query(
        client_ohne_token, "{ studenten(suchparameter: null) { id } }", headers
    )

    assert body == {"data": {"studenten": []}}
