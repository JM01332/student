"""REST-Schnittstelle der Student-Anwendung."""

from student.router.hello_router import router as hello_router
from student.router.student_router import get_by_id, student_router

__all__ = ["get_by_id", "hello_router", "student_router"]
