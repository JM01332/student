"""Rollen der Student-Anwendung."""

from enum import StrEnum


class Role(StrEnum):
    """Rollen für Administration und registrierte Studierende."""

    ADMIN = "ADMIN"
    STUDENT = "STUDENT"
