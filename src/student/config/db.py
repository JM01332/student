"""DB-URL und Verbindungsparameter für SQLAlchemy."""

from typing import Final

from loguru import logger
from sqlalchemy.engine import URL

from student.config.config import app_config, resources_path

__all__ = [
    "db_connect_args",
    "db_dialect",
    "db_log_statements",
    "db_url",
    "db_url_admin",
]

_db_toml: Final = app_config.get("db", {})

db_dialect: Final[str] = _db_toml.get("dialect", "postgresql")
"""DB-Dialekt für SQLAlchemy: 'postgresql'."""
logger.debug("db: db_dialect={}", db_dialect)

_dbname: Final[str] = _db_toml.get("name", "student")
_host: Final[str] = _db_toml.get("host", "postgres")
_username: Final[str] = _db_toml.get("username", "student")
_password: Final[str] = _db_toml.get("password", "Change Me!")
_password_admin: Final[str] = _db_toml.get("password-admin", "Change Me!")

db_log_statements: Final[bool] = bool(_db_toml.get("log-statements", False))
"""True, falls die SQL-Anweisungen protokolliert werden sollen."""

_connect_timeout: Final[int] = _db_toml.get("connect-timeout", 2)

db_url: Final[URL] = URL.create(
    drivername="postgresql+psycopg",
    username=_username,
    password=_password,
    host=_host,
    database=_dbname,
)
"""DB-URL für SQLAlchemy."""
logger.debug("db: db_url={}", db_url)

db_url_admin: Final[URL] = URL.create(
    drivername="postgresql+psycopg",
    username="postgres",
    password=_password_admin,
    host=_host,
    database=_dbname,
)
"""DB-URL für den Superuser, z.B. für COPY beim Neuladen der DB."""

db_connect_args: Final[dict[str, str]] = {
    "sslmode": "verify-full",
    "sslrootcert": str(resources_path / db_dialect / "server.crt"),
    # max. Wartezeit in Sekunden je Verbindungsversuch, sonst wartet psycopg
    # unbegrenzt, z.B. wenn der DB-Container gestoppt ist
    "connect_timeout": str(_connect_timeout),
}
"""Verbindungsparameter für TLS und Timeout bei PostgreSQL."""
logger.debug("db: db_connect_args={}", db_connect_args)
