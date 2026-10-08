"""Konfiguration aus der TOML-Datei einlesen."""

from importlib.resources import files
from pathlib import Path
from sys import stderr
from tomllib import load
from typing import Any, Final

from loguru import logger

__all__ = ["app_config", "resources_path"]

resources_path: Final = files("student.config") / "resources"
"""Verzeichnis mit app.toml und den TLS-Dateien."""

_config_file: Final = resources_path / "app.toml"

with _config_file.open("rb") as reader:
    app_config: Final[dict[str, Any]] = load(reader)

_logger_toml: Final = app_config.get("logger", {})
_logger_debug: Final[bool] = bool(_logger_toml.get("debug-level", False))

LOG_FILE: Final = Path("log") / "app.log"
if _logger_debug:
    logger.add(LOG_FILE, rotation="1 MB")
else:
    logger.remove()  # Standard-Ausgabe mit Level DEBUG entfernen
    logger.add(stderr, level="INFO")
    logger.add(LOG_FILE, rotation="1 MB", level="INFO")

logger.info("Logging ist konfiguriert")
logger.debug("config: _config_file={}", _config_file)
logger.debug("config: app_config={}", app_config)
