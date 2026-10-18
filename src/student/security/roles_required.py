"""Überprüfung der erforderlichen Rollen als FastAPI-Dependency."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from student.security.dependencies import get_token_service
from student.security.role import Role
lazy from student.security.token_service import TokenService

__all__ = ["RolesRequired"]


class RolesRequired:
    """Eine erforderliche Rolle oder eine beliebige Rolle aus einer Liste prüfen."""

    def __init__(self, required_roles: list[Role] | Role) -> None:
        """Erforderliche Rollen wie im Beispiel übernehmen."""
        self.required_roles = required_roles

    def __call__(
        self,
        request: Request,
        service: Annotated[TokenService, Depends(get_token_service)],
    ) -> None:
        """Benutzer prüfen und nur bei ausreichender Rolle im Request ablegen.

        Fehlende Rollen ergeben 403; AuthorizationError wird weitergereicht.
        Eine leere Liste erforderlicher Rollen erlaubt keinen Zugriff.
        Benutzerdaten, Header und Tokens werden nicht protokolliert.
        """
        user = service.get_user_from_request(request)
        if isinstance(self.required_roles, Role):
            if self.required_roles not in user.roles:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
            request.state.current_user = user
            return

        for role in user.roles:
            if role in self.required_roles:
                request.state.current_user = user
                return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
