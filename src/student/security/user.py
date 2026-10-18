"""Benutzerdaten für die Authentifizierung."""

from dataclasses import dataclass, field

lazy from student.security.role import Role


@dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class User:
    """Benutzerdaten mit Rollen und optionalem Passwort ohne repr-Ausgabe."""

    username: str
    email: str
    nachname: str
    vorname: str
    roles: list[Role]
    password: str | None = field(default=None, repr=False)
