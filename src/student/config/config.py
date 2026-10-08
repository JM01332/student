"""Konfiguration aus der TOML-Datei einlesen."""

from importlib.resources import files
from tomllib import load
from typing import Any, Final

__all__ = ["app_config", "resources_path"]

resources_path: Final = files("student.config") / "resources"
"""Verzeichnis mit app.toml und den TLS-Dateien."""

_config_file: Final = resources_path / "app.toml"

with _config_file.open("rb") as reader:
    app_config: Final[dict[str, Any]] = load(reader)
