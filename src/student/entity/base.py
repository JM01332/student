"""Basisklasse für Entity-Klassen."""

from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

__all__ = ["Base"]


class Base(MappedAsDataclass, DeclarativeBase):
    """Basisklasse für Entity-Klassen als dataclass."""
