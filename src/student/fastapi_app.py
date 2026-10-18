"""FastAPI-Anwendung für die Verwaltung von Studierendendaten."""

from contextlib import asynccontextmanager
from time import time
from typing import Final
lazy from collections.abc import AsyncGenerator, Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from student.config import dev_db_populate
from student.config.dev import db_populate, db_populate_router
from student.problem_details import ProblemDetails
from student.repository import engine
from student.router import (
    health_router,
    hello_router,
    student_router,
    student_write_router,
)
from student.security import AuthorizationError, LoginError, set_response_headers
from student.security.auth_router import router as auth_router
from student.service import (
    EmailExistsError,
    ForbiddenError,
    MatrikelnummerExistsError,
    NotFoundError,
    VersionOutdatedError,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """DB beim Start im Dev-Modus neu laden und beim Herunterfahren freigeben.

    Code vor `yield` läuft beim Start des Servers, Code danach beim Herunterfahren.

    :param _app: Die FastAPI-Anwendung (von FastAPI übergeben, hier nicht benötigt)
    """
    if dev_db_populate:
        db_populate()
    try:
        yield
    finally:
        logger.info("Der Server wird heruntergefahren")
        logger.info("Connection-Pool fuer die DB wird getrennt")
        engine.dispose()


app: Final = FastAPI(lifespan=lifespan)

app.add_middleware(GZipMiddleware, minimum_size=500)


@app.middleware("http")
async def log_request_header(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """HTTP-Methode und URL jedes Requests protokollieren.

    :param request: Injiziertes Request-Objekt
    :param call_next: nächste aufzurufende Middleware
    :return: Unverändertes Response-Objekt
    :rtype: Response
    """
    logger.debug("{} '{}'", request.method, request.url)
    return await call_next(request)


@app.middleware("http")
async def log_response_time(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Antwortzeit und Statuscode jedes Requests protokollieren.

    :param request: Injiziertes Request-Objekt
    :param call_next: nächste aufzurufende Middleware
    :return: Unverändertes Response-Objekt
    :rtype: Response
    """
    start: Final = time()
    response: Final = await call_next(request)
    duration_ms: Final = (time() - start) * 1000
    logger.debug(
        "Response time: {:.2f} ms, statuscode: {}",
        duration_ms,
        response.status_code,
    )
    return response


app.include_router(health_router, prefix="/health")
app.include_router(hello_router, prefix="/hello")
app.include_router(student_router, prefix="/rest")
app.include_router(student_write_router, prefix="/rest")
app.include_router(auth_router, prefix="/auth")

# Neuladen der DB per REST nur im Dev-Modus, wie im Beispielprojekt
if dev_db_populate:
    app.include_router(db_populate_router, prefix="/dev")


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Header-Daten beim Response für IT-Sicherheit setzen.

    :param request: Injiziertes Request-Objekt, das zunächst fertig verarbeitet wird
    :param call_next: nächste aufzurufende Middleware
    :return: Response-Objekt mit zusätzlichen Header-Daten
    :rtype: Response
    """
    response: Final[Response] = await call_next(request)
    set_response_headers(response)
    return response


@app.exception_handler(AuthorizationError)
def authorization_error_handler(
    _request: Request, _err: AuthorizationError
) -> Response:
    """Ungültige Tokens mit 401 und ProblemDetails beantworten."""
    return ProblemDetails.create(status_code=status.HTTP_401_UNAUTHORIZED).to_response()


@app.exception_handler(LoginError)
def login_error_handler(_request: Request, err: LoginError) -> Response:
    """Abgelehnte Zugangsdaten wie im Beispiel mit 401 beantworten."""
    return ProblemDetails.create(
        status_code=status.HTTP_401_UNAUTHORIZED, detail=str(err)
    ).to_response()


@app.exception_handler(ForbiddenError)
def forbidden_error_handler(_request: Request, _err: ForbiddenError) -> Response:
    """Verweigerten Datensatzzugriff mit 403 und ProblemDetails beantworten."""
    return ProblemDetails.create(status_code=status.HTTP_403_FORBIDDEN).to_response()


@app.exception_handler(NotFoundError)
def not_found_error_handler(_request: Request, err: NotFoundError) -> Response:
    """Errorhandler für NotFoundError aus der Geschäftslogik.

    :param _request: Request-Objekt (hier nicht benötigt)
    :param err: NotFoundError aus dem Service
    :return: Response mit Statuscode 404 und ProblemDetails
    :rtype: Response
    """
    logger.debug("NotFoundError: {}", vars(err))
    return ProblemDetails.create(status_code=status.HTTP_404_NOT_FOUND).to_response()


@app.exception_handler(EmailExistsError)
def email_exists_error_handler(_request: Request, err: EmailExistsError) -> Response:
    """Errorhandler für EmailExistsError beim Anlegen und Ändern.

    :param _request: Request-Objekt (hier nicht benötigt)
    :param err: Exception, falls die Emailadresse bereits existiert
    :return: Response mit Statuscode 422 und ProblemDetails
    :rtype: Response
    """
    return ProblemDetails.create(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(err),
    ).to_response()


@app.exception_handler(MatrikelnummerExistsError)
def matrikelnummer_exists_error_handler(
    _request: Request,
    err: MatrikelnummerExistsError,
) -> Response:
    """Errorhandler für MatrikelnummerExistsError beim Anlegen und Ändern.

    :param _request: Request-Objekt (hier nicht benötigt)
    :param err: Exception, falls die Matrikelnummer bereits existiert
    :return: Response mit Statuscode 422 und ProblemDetails
    :rtype: Response
    """
    return ProblemDetails.create(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(err),
    ).to_response()


@app.exception_handler(VersionOutdatedError)
def version_outdated_error_handler(
    _request: Request,
    err: VersionOutdatedError,
) -> Response:
    """Errorhandler für VersionOutdatedError beim Ändern.

    :param _request: Request-Objekt (hier nicht benötigt)
    :param err: Exception, falls die Versionsnummer zum Ändern veraltet ist
    :return: Response mit Statuscode 412 und ProblemDetails
    :rtype: Response
    """
    return ProblemDetails.create(
        status_code=status.HTTP_412_PRECONDITION_FAILED,
        detail=str(err),
    ).to_response()
