"""FastAPI-Anwendung mit dem ersten Demo-Endpunkt."""

from time import time
from typing import Final
lazy from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from student.router import hello_router, student_router
from student.security import set_response_headers

app: Final = FastAPI()

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


app.include_router(hello_router, prefix="/hello")
app.include_router(student_router, prefix="/rest")


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
