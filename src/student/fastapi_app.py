"""FastAPI-Anwendung mit dem ersten Demo-Endpunkt."""

from typing import Final

from fastapi import FastAPI

from student.router.hello_router import router as hello_router
from student.router.student_router import student_router

app: Final = FastAPI()
app.include_router(hello_router, prefix="/hello")
app.include_router(student_router, prefix="/rest")
