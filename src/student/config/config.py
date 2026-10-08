"""Konfiguration aus der TOML-Datei einlesen."""

from importlib.resources import files
from tomllib import load
from typing import Any, Final

__all__ = ["app_config"]

_config_file: Final = files("student.config") / "resources" / "app.toml"

with _config_file.open("rb") as reader:
    app_config: Final[dict[str, Any]] = load(reader)
