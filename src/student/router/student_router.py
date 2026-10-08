"""StudentRouter."""

from typing import Annotated, Any, Final

from fastapi import APIRouter, Depends, HTTPException, status

from student.router.dependencies import get_service
lazy from student.service import StudentService

__all__ = ["student_router"]

student_router: Final = APIRouter(tags=["Lesen"])


@student_router.get("/{student_id}")
def get_by_id(
    student_id: int,
    service: Annotated[StudentService, Depends(get_service)],
) -> dict[str, Any]:
    """Suche mit der Student-ID.

    :param student_id: ID des gesuchten Studierenden als Pfadparameter
    :param service: Injizierter Service für Geschäftslogik
    :return: Daten des gefundenen Studierenden
    :raises HTTPException: 404, falls es die ID nicht gibt
    """
    student: Final = service.find_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return student
