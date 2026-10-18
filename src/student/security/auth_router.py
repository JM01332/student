"""REST-Schnittstelle für Login ohne Protokollierung sensibler Daten."""

from json import JSONDecodeError
from typing import Annotated, Any, Final, cast

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from student.security.dependencies import get_token_service
from student.security.login_data import LoginData
lazy from student.security.token_service import TokenService

router: Final = APIRouter(tags=["Login"])


async def request_body_to_dict(request: Request) -> dict[str, Any]:
    """JSON manuell lesen, damit ungültige Login-Daten 401 statt 422 ergeben."""
    try:
        body = await request.json()
    except JSONDecodeError, UnicodeDecodeError:
        return {}
    return body if isinstance(body, dict) else {}


@router.api_route(path="/token", methods=["QUERY"])
def token(
    body: Annotated[dict[str, Any], Depends(request_body_to_dict)],
    service: Annotated[TokenService, Depends(get_token_service)],
) -> Response:
    """Zugangsdaten gegen Access Token, Ablaufzeit und Client-Rollen tauschen."""
    try:
        login_data = LoginData(**body)
    except TypeError:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    token_data = service.token(
        username=login_data.username,
        password=login_data.password,
    )
    access_token = cast("str", token_data["access_token"])
    user = service.get_user_from_token(token=access_token)
    return JSONResponse(
        content={
            "token": access_token,
            "expires_in": token_data["expires_in"],
            "rollen": user.roles,
        }
    )
