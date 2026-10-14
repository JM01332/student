"""Router zum Neuladen der DB im Modus DEV."""

from typing import Annotated, Final

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger

from student.config.dev.db_populate import DbPopulateService, get_db_populate_service
from student.problem_details import ProblemDetails

__all__ = ["router"]

router: Final = APIRouter(tags=["Admin"])


# TODO Mit Keycloak (#39) wie im Beispielprojekt nur für die Rolle Admin freigeben
@router.api_route(path="/db_populate", methods=["QUERY"])
async def populate(
    request: Request,
    service: Annotated[DbPopulateService, Depends(get_db_populate_service)],
) -> Response:
    """Die DB mit den Testdaten neu laden, z.B. vor den Integrationstests.

    :param request: Request-Objekt; der Body muss leer sein
    :param service: Injizierter Service zum Neuladen der DB
    :return: JSON-Datensatz mit der Erfolgsmeldung oder 400 bei nicht-leerem Body
    :rtype: Response
    """
    body: Final = await request.body()
    if len(body) > 0:
        logger.error("Kein leerer Request-Body")
        return ProblemDetails.create(
            status_code=status.HTTP_400_BAD_REQUEST,
        ).to_response()

    logger.warning("REST-Schnittstelle zum Neuladen der DB aufgerufen")
    service.populate()
    return JSONResponse(content={"db_populate": "success"})
