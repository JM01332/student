"""Datenklasse für die Login-Daten."""

from dataclasses import dataclass, field


@dataclass(frozen=True, eq=False, slots=True, kw_only=True)
class LoginData:
    """Benutzername und Passwort für die Token-Anforderung."""

    username: str
    password: str = field(repr=False)
