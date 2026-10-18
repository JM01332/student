"""Benutzermodell und Zuordnung der Keycloak-Rollennamen prüfen."""

import pytest

from student.security import Role, User


@pytest.mark.parametrize(
    ("claim", "expected"), [("admin", Role.ADMIN), ("student", Role.STUDENT)]
)
def test_keycloak_role_mapping(claim: str, expected: Role) -> None:
    assert Role[claim.upper()] is expected
    assert str(expected) == claim.upper()


def test_user_without_password() -> None:
    user = User(
        username="student",
        email="student@example.com",
        nachname="Muster",
        vorname="Max",
        roles=[Role.STUDENT],
    )
    assert user.password is None
    assert user.roles == [Role.STUDENT]


def test_password_is_not_in_repr() -> None:
    user = User(
        username="student",
        email="student@example.com",
        nachname="Muster",
        vorname="Max",
        roles=[Role.STUDENT],
        password="dummy-password",  # ruff: ignore[hardcoded-password-func-arg]
    )
    assert "dummy-password" not in repr(user)
    assert "password=" not in repr(user)
