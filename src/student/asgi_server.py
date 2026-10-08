"""Start der FastAPI-Anwendung mit Uvicorn."""

import uvicorn

from student.config import host_binding, port, tls_certfile, tls_keyfile

__all__ = ["run"]


def run() -> None:
    """Den lokalen Entwicklungsserver mit HTTPS starten."""
    uvicorn.run(
        "student:app",
        host=host_binding,
        port=port,
        ssl_keyfile=tls_keyfile,
        ssl_certfile=tls_certfile,
    )
