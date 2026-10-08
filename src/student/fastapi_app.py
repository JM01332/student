"""FastAPI-Anwendung mit dem ersten Demo-Endpunkt."""

from typing import Final

from fastapi import FastAPI

from student.router import hello_router, student_router

app: Final = FastAPI()
app.include_router(hello_router, prefix="/hello")
app.include_router(student_router, prefix="/rest")
