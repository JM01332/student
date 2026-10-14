"""Exceptions in der Geschäftslogik."""

__all__ = ["EmailExistsError", "MatrikelnummerExistsError", "NotFoundError"]


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
