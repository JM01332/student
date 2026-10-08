# Copyright (C) 2023 - present Juergen Zimmermann, Hochschule Karlsruhe
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


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
