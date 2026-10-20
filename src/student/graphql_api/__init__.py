"""GraphQL-Schnittstelle der Student-Anwendung."""

from student.graphql_api.graphql_types import (
    AdresseInput,
    CreatePayload,
    LoginResult,
    PruefungsleistungInput,
    StudentInput,
    Suchparameter,
)
from student.graphql_api.schema import Mutation, Query, graphql_router

__all__ = [
    "AdresseInput",
    "CreatePayload",
    "LoginResult",
    "Mutation",
    "PruefungsleistungInput",
    "Query",
    "StudentInput",
    "Suchparameter",
    "graphql_router",
]
