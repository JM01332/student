"""Eingabe-Typen für GraphQL."""

import strawberry

__all__ = ["Suchparameter"]


@strawberry.input
class Suchparameter:
    """Suchparameter für die Suche nach Studierenden."""

    nachname: str | None = None
    """Teil des Nachnamens als Suchkriterium."""

    email: str | None = None
    """Emailadresse als Suchkriterium."""
