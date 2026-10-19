"""Factories für den gemeinsam verwendeten TokenService und UserService."""

from functools import cache

from student.security.token_service import TokenService
from student.security.user_service import UserService


@cache
def get_token_service() -> TokenService:
    """TokenService für Dependency Injection bereitstellen."""
    return TokenService()


@cache
def get_user_service() -> UserService:
    """UserService für Dependency Injection bereitstellen.

    `@cache`: Das Objekt wird erst beim ersten Aufruf erzeugt (dann verbindet es
    sich mit Keycloak) und danach wiederverwendet.
    """
    return UserService()
