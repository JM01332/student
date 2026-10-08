"""Konfiguration für den privaten Schlüssel und das Zertifikat für TLS."""

from typing import Final

from student.config.config import app_config, resources_path

__all__ = ["tls_certfile", "tls_keyfile"]

_tls_toml: Final = app_config.get("tls", {})
_tls_path: Final = resources_path / "tls"

_key: Final[str] = _tls_toml.get("key", "key.pem")
tls_keyfile: Final[str] = str(_tls_path / _key)
"""Pfad zum privaten Schlüssel für TLS."""

_certificate: Final[str] = _tls_toml.get("certificate", "certificate.crt")
tls_certfile: Final[str] = str(_tls_path / _certificate)
"""Pfad zum Zertifikat für TLS."""
