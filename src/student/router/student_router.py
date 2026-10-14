"""StudentRouter."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from student.router.constants import ETAG, IF_NONE_MATCH, IF_NONE_MATCH_MIN_LEN
from student.router.dependencies import get_service
from student.router.student_find_model import StudentResponseModel
lazy from student.service import StudentService

__all__ = ["student_router"]

student_router: Final = APIRouter(tags=["Lesen"])


@student_router.get("/{student_id}", response_model=StudentResponseModel)
def get_by_id(
    student_id: int,
    request: Request,
    service: Annotated[StudentService, Depends(get_service)],
) -> Response:
    """Suche mit der Student-ID.

    :param student_id: ID des gesuchten Studierenden als Pfadparameter
    :param request: Request mit optionalem If-None-Match-Header
    :param service: Injizierter Service für Geschäftslogik
    :return: JSON mit ETag oder HTTP 304 ohne Body bei gleicher Version
    :rtype: Response
    :raises NotFoundError: Falls es die ID nicht gibt, als 404 durch den Handler
    """
    logger.debug("student_id={}", student_id)
    student: Final = service.find_by_id(student_id)
    headers: Final = {ETAG: f'"{student.version}"'}
    if_none_match: Final = request.headers.get(IF_NONE_MATCH)
    if (
        if_none_match is not None
        and len(if_none_match) >= IF_NONE_MATCH_MIN_LEN
        and if_none_match.startswith('"')
        and if_none_match.endswith('"')
    ):
        version = if_none_match[1:-1]
        try:
            if int(version) == student.version:
                return Response(
                    status_code=status.HTTP_304_NOT_MODIFIED,
                    headers=headers,
                )
        except ValueError:
            logger.debug("invalid version={}", version)

    return JSONResponse(
        content=StudentResponseModel.from_dto(student).model_dump(mode="json"),
        headers=headers,
    )


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
