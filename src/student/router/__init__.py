"""REST-Schnittstelle der Student-Anwendung."""

from student.router.health_router import liveness, readiness, router as health_router
from student.router.hello_router import router as hello_router
from student.router.student_router import get, get_by_id, student_router
from student.router.student_write_router import (
    delete_by_id,
    post,
    put,
    student_write_router,
)

__all__ = [
    "delete_by_id",
    "get",
    "get_by_id",
    "health_router",
    "hello_router",
    "liveness",
    "post",
    "put",
    "readiness",
    "student_router",
    "student_write_router",
]
