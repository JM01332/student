"""StudentRouter."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends
from loguru import logger

from student.router.dependencies import get_service
lazy from student.service import StudentDTO, StudentService

__all__ = ["student_router"]

student_router: Final = APIRouter(tags=["Lesen"])


@student_router.get("/{student_id}")
def get_by_id(
    student_id: int,
    service: Annotated[StudentService, Depends(get_service)],
) -> StudentDTO:
    """Suche mit der Student-ID.

    :param student_id: ID des gesuchten Studierenden als Pfadparameter
    :param service: Injizierter Service für Geschäftslogik
    :return: Daten des gefundenen Studierenden, von FastAPI als JSON ausgegeben
    :raises NotFoundError: Falls es die ID nicht gibt, als 404 durch den Handler
    """
    logger.debug("student_id={}", student_id)
    return service.find_by_id(student_id)


@student_router.get("")
def get(
    service: Annotated[StudentService, Depends(get_service)],
    nachname: str | None = None,
    email: str | None = None,
) -> list[StudentDTO]:
    """Suche mit Query-Parametern.

    :param service: Injizierter Service für Geschäftslogik
    :param nachname: Optionaler Query-Parameter für einen Teil des Nachnamens
    :param email: Optionaler Query-Parameter für die Emailadresse
    :return: Liste der gefundenen Studierenden
    :raises NotFoundError: Falls nichts gefunden wurde, als 404 durch den Handler
    """
    logger.debug("nachname={}, email={}", nachname, email)
    return service.find(nachname=nachname, email=email)
