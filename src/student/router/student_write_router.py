"""StudentWriteRouter: Studierende anlegen."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Request, Response, status
from loguru import logger

from student.router.dependencies import get_write_service
lazy from student.router.student_model import StudentModel
lazy from student.service import StudentWriteService

__all__ = ["student_write_router"]

student_write_router: Final = APIRouter(tags=["Schreiben"])


@student_write_router.post("")
def post(
    student_model: StudentModel,
    request: Request,
    service: Annotated[StudentWriteService, Depends(get_write_service)],
) -> Response:
    """POST-Request, um einen neuen Studierenden anzulegen.

    :param student_model: Daten des neuen Studierenden, von pydantic validiert
    :param request: Request-Objekt mit der URL für den Location-Header
    :param service: Injizierter Service zum Schreiben
    :return: Response mit Statuscode 201 und Location-Header, ohne Body
    :rtype: Response
    :raises ValidationError: Bei ungültigen Daten, als 422 durch FastAPI
    :raises EmailExistsError: Falls die Emailadresse bereits existiert
    :raises MatrikelnummerExistsError: Falls die Matrikelnummer bereits existiert
    """
    logger.debug("student_model={}", student_model)
    student_dto: Final = service.create(student=student_model.to_student())
    logger.debug("student_dto={}", student_dto)
    return Response(
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"{request.url}/{student_dto.id}"},
    )
