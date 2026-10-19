"""Router zum Neuladen der Keycloak-Benutzer im Modus DEV."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from student.config.dev.keycloak_populate import (
    KeycloakPopulateService,
    get_keycloak_populate_service,
)
from student.problem_details import ProblemDetails
from student.security import Role, RolesRequired

__all__ = ["router"]

router: Final = APIRouter(tags=["Admin"])


@router.api_route(
    path="/keycloak_populate",
    methods=["QUERY"],
    dependencies=[Depends(RolesRequired(Role.ADMIN))],
)
async def populate(
    request: Request,
    service: Annotated[KeycloakPopulateService, Depends(get_keycloak_populate_service)],
) -> Response:
    """Die Keycloak-Benutzer passend zu den Testdaten neu laden.

    :param request: Request-Objekt; der Body muss leer sein
    :param service: Injizierter Service zum Neuladen von Keycloak
    :return: JSON-Datensatz mit der Erfolgsmeldung oder 400 bei nicht-leerem Body
    :rtype: Response
    """
    body: Final = await request.body()
    if len(body) > 0:
        logger.error("Kein leerer Request-Body")
        return ProblemDetails.create(
            status_code=status.HTTP_400_BAD_REQUEST,
        ).to_response()

    logger.warning(
        "REST-Schnittstelle zum Neuladen von Keycloak aufgerufen von {}",
        request.state.current_user.username,
    )
    service.populate()
    return JSONResponse(content={"keycloak_populate": "success"})
