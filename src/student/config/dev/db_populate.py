"""Neuladen der DB im Modus DEV."""

from re import match
from string import Template
from typing import Final

from loguru import logger
from sqlalchemy import Connection, create_engine, text

from student.config.config import resources_path
from student.config.db import (
    db_connect_args,
    db_dialect,
    db_log_statements,
    db_url_admin,
)
from student.config.dev_modus import dev_db_populate
from student.repository import engine

__all__ = ["DbPopulateService", "db_populate", "get_db_populate_service"]

_TABELLEN: Final = ["student", "adresse", "pruefungsleistung"]
"""Tabellen in der Reihenfolge, in der die CSV-Dateien geladen werden."""

_CSV_PATH: Final = "/init/student/csv"
"""Verzeichnis der CSV-Dateien im DB-Server (Volume pg_init)."""


class DbPopulateService:
    """Neuladen der DB im Modus DEV."""

    def __init__(self) -> None:
        """Initialisierung von `Engine` für SQLAlchemy mit dem Admin-User."""
        self.engine_admin: Final = create_engine(
            db_url_admin,
            connect_args=db_connect_args,
            echo=db_log_statements,
        )

    def populate(self) -> None:
        """DB mit drop.sql, create.sql und den CSV-Dateien neu laden."""
        if not dev_db_populate:
            return

        logger.warning(">>> Die DB wird neu geladen: {} <<<", engine.url)
        dialect_path: Final = resources_path / db_dialect
        with engine.connect() as connection:
            for dateiname in ("drop.sql", "create.sql"):
                inhalt = (dialect_path / dateiname).read_text(encoding="utf-8")
                zeilen = self._remove_comment(inhalt.splitlines(keepends=True))
                for stmt in self._build_sql_statements(zeilen):
                    connection.execute(text(stmt))
            connection.commit()
        engine.dispose()
        self._load_csv_files()
        logger.warning(">>> Die DB wurde neu geladen <<<")

    def _remove_comment(self, zeilen: list[str]) -> list[str]:
        """SQL-Kommentare und Leerzeilen entfernen."""
        return [
            zeile for zeile in zeilen if not match(r"^ *--", zeile) and zeile != "\n"
        ]

    def _build_sql_statements(self, zeilen: list[str]) -> list[str]:
        """Zeilen mit SQL-Anweisungen zu je einer Anweisung zusammenfassen."""
        statements: list[str] = []
        sql = ""
        for zeile in zeilen:
            sql += zeile.replace("\n", " ")
            if zeile.endswith(";\n"):
                statements.append(sql)
                sql = ""
        return statements

    def _load_csv_files(self) -> None:
        """CSV-Dateien als Superuser per COPY in die Tabellen laden."""
        with self.engine_admin.connect() as connection:
            connection.execute(text("SET search_path TO student;"))
            for tabelle in _TABELLEN:
                self._load_csv_file(tabelle=tabelle, connection=connection)
            connection.commit()
        self.engine_admin.dispose()

    def _load_csv_file(self, tabelle: str, connection: Connection) -> None:
        """Eine CSV-Datei per COPY in die gleichnamige Tabelle laden."""
        logger.debug("tabelle={}", tabelle)
        copy_cmd: Final = Template(
            "COPY ${TABELLE} FROM '"
            + _CSV_PATH
            + "/${TABELLE}.csv' (FORMAT csv, QUOTE '\"', DELIMITER ';', HEADER true);",
        ).substitute(TABELLE=tabelle)
        connection.execute(text(copy_cmd))


def get_db_populate_service() -> DbPopulateService:
    """Factory-Funktion für DbPopulateService."""
    return DbPopulateService()


def db_populate() -> None:
    """DB mit Testdaten neu laden, falls im Dev-Modus."""
    if dev_db_populate:
        get_db_populate_service().populate()
