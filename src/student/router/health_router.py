"""HealthRouter: Liveness und Readiness des Servers."""

from typing import Final

from fastapi import APIRouter
from loguru import logger
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from student.repository import engine

__all__ = ["router"]

router: Final = APIRouter(tags=["Health"])


@router.get("/liveness")
def liveness() -> dict[str, str]:
    """Überprüfen der Liveness: Der Server läuft und beantwortet Requests.

    :return: JSON-Datensatz mit der Statusmeldung
    :rtype: dict[str, str]
    """
    return {"status": "up"}


@router.get("/readiness")
def readiness() -> dict[str, str]:
    """Überprüfen der Readiness: Der Server erreicht die Datenbank.

    :return: JSON-Datensatz mit dem Status der Datenbank
    :rtype: dict[str, str]
    """
    # Auch der Verbindungsaufbau steht im try-Block: Ist die DB nicht erreichbar,
    # scheitert bereits engine.connect()
    try:
        with engine.connect() as connection:
            connection.scalar(text("SELECT 1"))
    except OperationalError:
        logger.warning("Readiness: Datenbank nicht erreichbar")
        return {"db": "down"}
    return {"db": "up"}
