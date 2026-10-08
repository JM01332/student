"""Start der FastAPI-Anwendung mit Uvicorn."""

from pathlib import Path
from typing import Final

import uvicorn

from student.config import host_binding, port

__all__ = ["run"]

_TLS_PATH: Final = Path(__file__).parent / "config" / "resources" / "tls"


def run() -> None:
    """Den lokalen Entwicklungsserver mit HTTPS auf Port 8000 starten."""
    uvicorn.run(
        "student:app",
        host=host_binding,
        port=port,
        ssl_keyfile=_TLS_PATH / "key.pem",
        ssl_certfile=_TLS_PATH / "certificate.crt",
    )
