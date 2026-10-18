"""Factory für den gemeinsam verwendeten TokenService."""

from functools import cache

from student.security.token_service import TokenService


@cache
def get_token_service() -> TokenService:
    """TokenService für Dependency Injection bereitstellen."""
    return TokenService()
