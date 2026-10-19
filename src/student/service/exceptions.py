"""Exceptions in der Geschäftslogik."""

__all__ = [
    "EmailExistsError",
    "EmptyUsernameError",
    "ForbiddenError",
    "MatrikelnummerExistsError",
    "NotFoundError",
    "UsernameExistsError",
    "VersionOutdatedError",
]


class EmailExistsError(Exception):
    """Exception, falls die Emailadresse bereits existiert."""

    def __init__(self, email: str) -> None:
        """Initialisierung von EmailExistsError mit der Emailadresse.

        :param email: Bereits existierende Emailadresse
        """
        super().__init__(f"Existierende Email: {email}")
        self.email = email


class MatrikelnummerExistsError(Exception):
    """Exception, falls die Matrikelnummer bereits existiert."""

    def __init__(self, matrikelnummer: str) -> None:
        """Initialisierung von MatrikelnummerExistsError mit der Matrikelnummer.

        :param matrikelnummer: Bereits existierende Matrikelnummer
        """
        super().__init__(f"Existierende Matrikelnummer: {matrikelnummer}")
        self.matrikelnummer = matrikelnummer


class EmptyUsernameError(ValueError):
    """Exception, falls der Benutzername fehlt (z.B. beim Anlegen)."""

    def __init__(self) -> None:
        """Initialisierung von EmptyUsernameError."""
        super().__init__("username ist None oder leer")


class UsernameExistsError(Exception):
    """Exception, falls der Benutzername in Keycloak bereits existiert."""

    def __init__(self, username: str) -> None:
        """Initialisierung von UsernameExistsError mit dem Benutzernamen.

        :param username: Bereits existierender Benutzername
        """
        super().__init__(f"Existierender Benutzername: {username}")
        self.username = username


class ForbiddenError(Exception):
    """Exception, falls der Zugriff auf den Datensatz nicht erlaubt ist."""


class NotFoundError(Exception):
    """Exception, falls keine Studierenden gefunden wurden."""

    def __init__(
        self,
        student_id: int | None = None,
        nachname: str | None = None,
        email: str | None = None,
    ) -> None:
        """Initialisierung von NotFoundError mit ID bzw. Suchparametern.

        :param student_id: ID, zu der kein Studierender gefunden wurde
        :param nachname: Suchparameter Nachname, zu dem nichts gefunden wurde
        :param email: Suchparameter Email, zu dem nichts gefunden wurde
        """
        super().__init__("Not Found")
        self.student_id = student_id
        self.nachname = nachname
        self.email = email


class VersionOutdatedError(Exception):
    """Exception, falls die Versionsnummer beim Aktualisieren veraltet ist."""

    def __init__(self, version: int) -> None:
        """Initialisierung von VersionOutdatedError mit veralteter Versionsnummer.

        :param version: Veraltete Versionsnummer aus dem If-Match-Header
        """
        super().__init__(f"Veraltete Version: {version}")
        self.version = version
