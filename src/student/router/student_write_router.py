"""StudentWriteRouter: Studierende anlegen und ändern."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Request, Response, status
from loguru import logger

from student.problem_details import ProblemDetails
from student.router.constants import ETAG, IF_MATCH, IF_MATCH_MIN_LEN
from student.router.dependencies import get_write_service
lazy from student.router.student_model import StudentModel
lazy from student.router.student_update_model import StudentUpdateModel
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


@student_write_router.put("/{student_id}")
def put(
    student_id: int,
    student_update_model: StudentUpdateModel,
    request: Request,
    service: Annotated[StudentWriteService, Depends(get_write_service)],
) -> Response:
    """PUT-Request, um einen Studierenden zu aktualisieren.

    :param student_id: ID des zu aktualisierenden Studierenden als Pfadparameter
    :param student_update_model: Neue Daten, von pydantic validiert
    :param request: Request-Objekt mit If-Match im Header
    :param service: Injizierter Service zum Schreiben
    :return: Response mit Statuscode 204 und neuem ETag, ohne Body
    :rtype: Response
    :raises ValidationError: Bei ungültigen Daten, als 422 durch FastAPI
    :raises NotFoundError: Falls zur ID kein Studierender existiert
    :raises VersionOutdatedError: Falls die Versionsnummer nicht aktuell ist
    :raises EmailExistsError: Falls die neue Emailadresse bereits existiert
    :raises MatrikelnummerExistsError: Falls die neue Matrikelnummer bereits existiert
    """
    if_match_value: Final = request.headers.get(IF_MATCH)
    logger.debug(
        "student_id={}, if_match={}, student_update_model={}",
        student_id,
        if_match_value,
        student_update_model,
    )

    # 428: Ohne If-Match könnte man versehentlich fremde Änderungen überschreiben
    if if_match_value is None:
        return ProblemDetails.create(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
        ).to_response()

    if (
        len(if_match_value) < IF_MATCH_MIN_LEN
        or not if_match_value.startswith('"')
        or not if_match_value.endswith('"')
    ):
        return ProblemDetails.create(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
        ).to_response()

    version: Final = if_match_value[1:-1]
    try:
        version_int: Final = int(version)
    except ValueError:
        return ProblemDetails.create(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
        ).to_response()

    student_dto: Final = service.update(
        student=student_update_model.to_student(),
        student_id=student_id,
        version=version_int,
    )
    logger.debug("student_dto={}", student_dto)
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={ETAG: f'"{student_dto.version}"'},
    )
