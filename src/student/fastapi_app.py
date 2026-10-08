"""FastAPI-Anwendung mit dem ersten Demo-Endpunkt."""

from typing import Final

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from student.router import hello_router, student_router

app: Final = FastAPI()

app.add_middleware(GZipMiddleware, minimum_size=500)

app.include_router(hello_router, prefix="/hello")
app.include_router(student_router, prefix="/rest")
