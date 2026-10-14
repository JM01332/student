"""Parameter für Pagination."""

from dataclasses import dataclass

__all__ = ["Pageable"]


@dataclass(eq=False, slots=True, kw_only=True)
class Pageable:
    """Seiteneinteilung für bereits validierte Parameter."""

    size: int
    """Anzahl Datensätze pro Seite; 0 bedeutet unbegrenzt."""

    number: int
    """Seitennummer, beginnend bei 0."""
