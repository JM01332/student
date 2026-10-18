"""Exceptions beim Zugriffsschutz."""


class LoginError(Exception):
    """Exception, falls Benutzername oder Passwort fehlerhaft ist."""

    def __init__(self, username: str | None = None) -> None:
        """LoginError mit dem betroffenen Benutzernamen initialisieren."""
        super().__init__(f"Fehlerhafte Benutzerdaten fuer {username}")
        self.username = username
