"""Exceptions in der Geschäftslogik."""

__all__ = ["NotFoundError"]


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
