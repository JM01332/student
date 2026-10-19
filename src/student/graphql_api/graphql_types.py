"""Eingabe- und Ergebnis-Typen für GraphQL."""

lazy from decimal import Decimal

import strawberry

__all__ = [
    "AdresseInput",
    "CreatePayload",
    "LoginResult",
    "PruefungsleistungInput",
    "StudentInput",
    "Suchparameter",
]


@strawberry.input
class Suchparameter:
    """Suchparameter für die Suche nach Studierenden."""

    nachname: str | None = None
    """Teil des Nachnamens als Suchkriterium."""

    email: str | None = None
    """Emailadresse als Suchkriterium."""


@strawberry.input
class AdresseInput:
    """Adresse eines neuen Studierenden."""

    plz: str
    """Postleitzahl."""

    ort: str
    """Ort."""


@strawberry.input
class PruefungsleistungInput:
    """Prüfungsleistung eines neuen Studierenden."""

    modul: str
    """Name des Moduls."""

    note: Decimal
    """Note, z.B. 1.3."""

    semester: str
    """Semester, z.B. "WS 2026/27" oder "SS 2026"."""


@strawberry.input
class StudentInput:
    """Daten für einen neuen Studierenden (wie der Request-Body bei POST)."""

    matrikelnummer: str
    """6-stellige Matrikelnummer."""

    nachname: str
    """Nachname."""

    vorname: str
    """Vorname."""

    email: str
    """Emailadresse."""

    username: str
    """Benutzername für Keycloak."""

    adresse: AdresseInput
    """Adresse."""

    pruefungsleistungen: list[PruefungsleistungInput]
    """Prüfungsleistungen, ggf. leer."""


@strawberry.type
class CreatePayload:
    """Ergebnis, wenn ein neuer Studierender angelegt wurde."""

    id: int
    """ID des neu angelegten Studierenden."""


@strawberry.type
class LoginResult:
    """Ergebnis eines erfolgreichen Logins."""

    token: str
    """Access Token des eingeloggten Benutzers."""

    expires_in: int
    """Gültigkeitsdauer des Tokens in Sekunden (im Schema: expiresIn)."""

    roles: list[str]
    """Rollen des eingeloggten Benutzers."""
