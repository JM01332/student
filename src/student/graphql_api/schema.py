"""Schema für GraphQL durch Strawberry ("Code-first")."""

from typing import Final
lazy from collections.abc import Sequence

import strawberry
from fastapi import Request
from loguru import logger
from strawberry.fastapi import GraphQLRouter
lazy from strawberry.types import Info

from student.config.graphql import graphql_ide
from student.repository import StudentRepository
from student.security import Role, TokenService
from student.service import NotFoundError, StudentDTO, StudentService
lazy from student.graphql_api.graphql_types import Suchparameter

__all__ = ["graphql_router"]

# Wie im Beispielprojekt einmal beim Laden des Moduls erzeugt
_repo: Final = StudentRepository()
_service: Final = StudentService(repo=_repo)
_token_service: Final = TokenService()


@strawberry.type  # vgl. @dataclass
class Query:
    """Queries, um Studierendendaten zu lesen."""

    @strawberry.field
    def student(self, student_id: strawberry.ID, info: Info) -> StudentDTO | None:
        """Daten zu einem Studierenden lesen.

        :param student_id: ID des gesuchten Studierenden
        :param info: Kontext mit dem Request und damit dem Authorization-Header
        :return: Gesuchter Studierender oder None, falls es die ID nicht gibt
        :rtype: StudentDTO | None
        :raises AuthorizationError: Ohne gültiges Token, wird zu einem GraphQL-Fehler
        :raises ForbiddenError: Bei fremdem Datensatz, wird zu einem GraphQL-Fehler
        """
        logger.debug("student_id={}", student_id)
        request: Final[Request] = info.context["request"]
        user: Final = _token_service.get_user_from_request(request=request)

        try:
            student_dto: Final = _service.find_by_id(
                student_id=int(student_id),
                user=user,
            )
        except NotFoundError:
            return None
        logger.debug("{}", student_dto)
        return student_dto

    @strawberry.field
    def studenten(
        self,
        suchparameter: Suchparameter | None,
        info: Info,
    ) -> Sequence[StudentDTO]:
        """Studierende anhand von Suchparametern suchen (nur Rolle admin).

        :param suchparameter: Teil des Nachnamens und/oder Emailadresse
        :param info: Kontext mit dem Request und damit dem Authorization-Header
        :return: Die gefundenen Studierenden, ggf. eine leere Liste
        :rtype: Sequence[StudentDTO]
        :raises AuthorizationError: Ohne gültiges Token, wird zu einem GraphQL-Fehler
        """
        logger.debug("suchparameter={}", suchparameter)
        request: Final[Request] = info.context["request"]
        user: Final = _token_service.get_user_from_request(request=request)
        if Role.ADMIN not in user.roles:
            return []

        try:
            # ohne Pageable: alle Treffer wie im Beispiel (dort size=0)
            studenten_dto: Final = _service.find(
                nachname=None if suchparameter is None else suchparameter.nachname,
                email=None if suchparameter is None else suchparameter.email,
            )
        except NotFoundError:
            return []
        logger.debug("{}", studenten_dto)
        return studenten_dto


schema: Final = strawberry.Schema(query=Query)

Context = dict[str, Request]
"""Kontext für die Resolver: der aktuelle Request (z.B. für den Bearer-Token)."""


def get_context(request: Request) -> Context:
    """Den Request für die Resolver im Kontext bereitstellen."""
    return {"request": request}


graphql_router: Final = GraphQLRouter[Context](
    schema,
    context_getter=get_context,
    graphql_ide=graphql_ide,
)
