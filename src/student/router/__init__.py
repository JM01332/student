"""REST-Schnittstelle der Student-Anwendung."""

from student.router.health_router import liveness, readiness, router as health_router
from student.router.hello_router import router as hello_router
from student.router.student_router import get, get_by_id, student_router

__all__ = [
    "get",
    "get_by_id",
    "health_router",
    "hello_router",
    "liveness",
    "readiness",
    "student_router",
]
