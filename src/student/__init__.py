"""Python-Paket und Server-Einstiegspunkt für die Student-Anwendung."""

from student.asgi_server import run
from student.fastapi_app import app

__all__ = ["app", "main"]


def main() -> None:  # ruff: ignore[non-empty-init-module]
    """Die Anwendung über das Skript `student` starten."""
    run()
