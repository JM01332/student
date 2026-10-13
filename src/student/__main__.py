"""CLI für das Projekt, damit das Paket als Python-Skript ausgeführt werden kann.

Aufruf: `uv run python -m student`. Das ist gleichwertig zu `uv run student`, braucht
aber nicht die von uv erzeugte `student.exe`, die Windows (Smart App Control)
blockieren kann. Wie im FastAPI-Beispiel eignet sich der Aufruf auch für ein
Docker-Image, in dem uv zur Laufzeit nicht benötigt wird.
"""

from student.asgi_server import run

__all__ = ["run"]

if __name__ == "__main__":
    run()
