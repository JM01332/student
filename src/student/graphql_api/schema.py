"""Schema für GraphQL durch Strawberry ("Code-first")."""

from dataclasses import asdict
from typing import Final, cast
lazy from collections.abc import Sequence

import strawberry
from fastapi import Request
from loguru import logger
from strawberry.extensions import PydanticErrorExtension
from strawberry.fastapi import GraphQLRouter
lazy from strawberry.types import Info

from student.config.graphql import graphql_ide
from student.graphql_api.graphql_types import CreatePayload, LoginResult
from student.repository import StudentRepository
from student.router.student_model import StudentModel
from student.security import Role, TokenService, UserService
from student.service import (
    ForbiddenError,
    NotFoundError,
    StudentDTO,
    StudentService,
    StudentWriteService,
)
lazy from student.graphql_api.graphql_types import StudentInput, Suchparameter

__all__ = ["graphql_router"]

# Wie im Beispielprojekt einmal beim Laden des Moduls erzeugt.
# UserService() verbindet sich dabei mit Keycloak; ohne Keycloak wird nur geloggt.
_repo: Final = StudentRepository()
_service: Final = StudentService(repo=_repo)
_user_service: Final = UserService()
_write_service: Final = StudentWriteService(repo=_repo, user_service=_user_service)
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


@strawberry.type
class Mutation:
    """Mutations, um Studierendendaten anzulegen, und Login."""

    @strawberry.mutation
    def create(self, student_input: StudentInput, info: Info) -> CreatePayload:
        """Einen neuen Studierenden anlegen (nur Rolle admin wie bei REST).

        :param student_input: Daten des neuen Studierenden
        :param info: Kontext mit dem Request und damit dem Authorization-Header
        :return: ID des neuen Studierenden
        :rtype: CreatePayload
        :raises AuthorizationError: Ohne gültiges Token
        :raises ForbiddenError: Ohne Rolle admin (Abweichung: im Beispiel ungeschützt)
        :raises ValidationError: Bei ungültigen Daten, über PydanticErrorExtension
        :raises EmailExistsError: Falls die Emailadresse bereits existiert
        :raises UsernameExistsError: Falls der Benutzername bereits existiert
        """
        logger.debug("student_input={}", student_input)
        request: Final[Request] = info.context["request"]
        user: Final = _token_service.get_user_from_request(request=request)
        if Role.ADMIN not in user.roles:
            raise ForbiddenError

        # Dictionary mit denselben pydantic-Regeln wie beim REST-POST validieren
        student_model: Final = StudentModel.model_validate(asdict(student_input))
        student_dto: Final = _write_service.create(student=student_model.to_student())
        payload: Final = CreatePayload(id=student_dto.id)
        logger.debug("{}", payload)
        return payload

    # Mutation, weil ein Login z.B. den Login-Zeitpunkt speichern könnte
    @strawberry.mutation
    def login(self, username: str, password: str) -> LoginResult:
        """Ein Token zu Benutzername und Passwort von Keycloak holen.

        :param username: Benutzername
        :param password: Passwort (wird nicht protokolliert)
        :return: Token mit Laufzeit in Sekunden und Rollen
        :rtype: LoginResult
        :raises LoginError: Bei falschen Zugangsdaten
        """
        logger.debug("username={}", username)
        token_mapping: Final = _token_service.token(
            username=username, password=password
        )
        token: Final = cast("str", token_mapping["access_token"])
        user: Final = _token_service.get_user_from_token(token)
        return LoginResult(
            token=token,
            # echte Laufzeit wie beim REST-Login statt fest "1d" wie im Beispiel
            expires_in=cast("int", token_mapping["expires_in"]),
            roles=[role.value for role in user.roles],
        )


schema: Final = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    # ValidationError von pydantic als lesbaren GraphQL-Fehler ausgeben
    extensions=[PydanticErrorExtension],
)

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
