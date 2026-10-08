"""StudentRouter."""

from typing import Annotated, Any, Final

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from student.router.dependencies import get_service
lazy from student.service import StudentService

__all__ = ["student_router"]

student_router: Final = APIRouter(tags=["Lesen"])


@student_router.get("/{student_id}")
def get_by_id(
    student_id: int,
    service: Annotated[StudentService, Depends(get_service)],
) -> dict[str, Any]:
    """Suche mit der Student-ID.

    :param student_id: ID des gesuchten Studierenden als Pfadparameter
    :param service: Injizierter Service für Geschäftslogik
    :return: Daten des gefundenen Studierenden
    :raises HTTPException: 404, falls es die ID nicht gibt
    """
    logger.debug("student_id={}", student_id)
    student: Final = service.find_by_id(student_id)
    if student is None:
        logger.debug("Kein Student mit der ID {}", student_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return student


@student_router.get("")
def get(
    service: Annotated[StudentService, Depends(get_service)],
    nachname: str | None = None,
    email: str | None = None,
) -> list[dict[str, Any]]:
    """Suche mit Query-Parametern.

    :param service: Injizierter Service für Geschäftslogik
    :param nachname: Optionaler Query-Parameter für einen Teil des Nachnamens
    :param email: Optionaler Query-Parameter für die Emailadresse
    :return: Liste der gefundenen Studierenden
    :raises HTTPException: 404, falls keine Studierenden gefunden wurden
    """
    logger.debug("nachname={}, email={}", nachname, email)
    studenten: Final = service.find(nachname=nachname, email=email)
    if not studenten:
        logger.debug("Keine Studierenden gefunden")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return studenten
