"""StudentRouter."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends
from loguru import logger

from student.router.dependencies import get_service
from student.router.student_find_model import StudentResponseModel
lazy from student.service import StudentService

__all__ = ["student_router"]

student_router: Final = APIRouter(tags=["Lesen"])


@student_router.get("/{student_id}", response_model=StudentResponseModel)
def get_by_id(
    student_id: int,
    service: Annotated[StudentService, Depends(get_service)],
) -> StudentResponseModel:
    """Suche mit der Student-ID.

    :param student_id: ID des gesuchten Studierenden als Pfadparameter
    :param service: Injizierter Service für Geschäftslogik
    :return: Daten des gefundenen Studierenden als Response-Modell
    :rtype: StudentResponseModel
    :raises NotFoundError: Falls es die ID nicht gibt, als 404 durch den Handler
    """
    logger.debug("student_id={}", student_id)
    student: Final = service.find_by_id(student_id)
    return StudentResponseModel.from_dto(student)


@student_router.get("", response_model=list[StudentResponseModel])
def get(
    service: Annotated[StudentService, Depends(get_service)],
    nachname: str | None = None,
    email: str | None = None,
) -> list[StudentResponseModel]:
    """Suche mit Query-Parametern.

    :param service: Injizierter Service für Geschäftslogik
    :param nachname: Optionaler Query-Parameter für einen Teil des Nachnamens
    :param email: Optionaler Query-Parameter für die Emailadresse
    :return: Liste der gefundenen Studierenden als Response-Modelle
    :rtype: list[StudentResponseModel]
    :raises NotFoundError: Falls nichts gefunden wurde, als 404 durch den Handler
    """
    logger.debug("nachname={}, email={}", nachname, email)
    studenten: Final = service.find(nachname=nachname, email=email)
    return [StudentResponseModel.from_dto(student) for student in studenten]
