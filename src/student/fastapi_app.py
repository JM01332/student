"""FastAPI-Anwendung mit dem ersten Demo-Endpunkt."""

from typing import Final
lazy from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware

from student.router import hello_router, student_router
from student.security import set_response_headers

app: Final = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=500)

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
