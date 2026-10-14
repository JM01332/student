"""Parameter für Pagination."""

from dataclasses import dataclass

__all__ = ["DEFAULT_PAGE_NUMBER", "DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE", "Pageable"]

DEFAULT_PAGE_NUMBER = 0
DEFAULT_PAGE_SIZE = 5
MAX_PAGE_SIZE = 100


@dataclass(eq=False, slots=True, kw_only=True)
class Pageable:
    """Seiteneinteilung für bereits validierte Parameter."""

    size: int
    """Anzahl Datensätze pro Seite; 0 bedeutet unbegrenzt."""

    number: int
    """Seitennummer, beginnend bei 0."""
