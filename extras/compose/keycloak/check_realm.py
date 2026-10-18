"""Lokalen Student-Realm prüfen, ohne Benutzer oder Konfiguration zu verändern."""

import base64
import json
import ssl
from http import HTTPStatus
from pathlib import Path

import httpx
from dotenv import dotenv_values

BASE_URL = "https://localhost:8843"
ISSUER = f"{BASE_URL}/realms/student"
CLIENT_ID = "student-client"
ROOT = Path(__file__).resolve().parents[3]
TOKEN_LIFESPAN = 30 * 60


def require(condition: bool, message: str) -> None:  # ruff: ignore[boolean-type-hint-positional-argument]
    """Bei einem fehlgeschlagenen Prüfschritt sofort abbrechen."""
    if not condition:
        raise SystemExit(message)


def check_user(client: httpx.Client, secret: str, username: str) -> None:
    """Token über geprüftes TLS anfordern und erwartete Claims vergleichen."""
    credentials = {"client_id": CLIENT_ID, "client_secret": secret}
    response = client.post(
        f"{ISSUER}/protocol/openid-connect/token",
        data={
            **credentials,
            "grant_type": "password",
            "username": username,
            "password": "p",
        },
    )
    require(
        response.status_code == HTTPStatus.OK,
        f"{username}: Token HTTP {response.status_code}",
    )
    token_data = response.json()
    token = token_data["access_token"]
    require(bool(token_data.get("refresh_token")), f"{username}: Refresh Token fehlt")

    # Nur die direkt über geprüftes TLS bezogene Tokenantwort auswerten.
    # Keine JWT-Signaturprüfung: nicht für Bearer-Tokens aus API-Requests verwenden.
    payload = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    require(claims.get("iss") == ISSUER, f"{username}: falscher Issuer")
    require(claims.get("azp") == CLIENT_ID, f"{username}: falscher Client")
    require(claims.get("preferred_username") == username, "Falscher Benutzer")
    require(claims.get("email") == f"{username}@acme.com", f"{username}: falsche Email")
    require(
        claims["exp"] - claims["iat"] == TOKEN_LIFESPAN,
        "Token-Laufzeit ist nicht 30 Minuten",
    )
    resources = claims.get("resource_access", {})
    roles = set(resources.get(CLIENT_ID, {}).get("roles", []))
    require(roles == {username}, f"{username}: unerwartete Student-Client-Rollen")
    admin_roles = set(resources.get("realm-management", {}).get("roles", []))
    if username == "admin":
        require(
            {"manage-users", "query-users", "realm-admin", "view-users"} <= admin_roles,
            "admin: Verwaltungsrollen fehlen",
        )
    else:
        require(not admin_roles, "student: unerwartete Verwaltungsrollen")
    print(
        f"{username}: Token ausgestellt, Claims und Rollen korrekt, Laufzeit 30 Minuten"
    )


def main() -> None:
    """Discovery und beide lokale Testzugänge mit geprüftem TLS testen."""
    secret = dotenv_values(ROOT / ".env").get("CLIENT_SECRET")
    require(bool(secret), "CLIENT_SECRET fehlt in der lokalen .env")
    if not secret:
        return
    context = ssl.create_default_context(
        cafile=ROOT / "extras/compose/keycloak/tls/certificate.crt",
    )
    with httpx.Client(verify=context, timeout=10, trust_env=False) as client:
        response = client.get(f"{ISSUER}/.well-known/openid-configuration")
        require(
            response.status_code == HTTPStatus.OK,
            f"Discovery HTTP {response.status_code}",
        )
        discovery = response.json()
        require(discovery.get("issuer") == ISSUER, "Discovery: falscher Issuer")
        require(
            discovery.get("token_endpoint")
            == f"{ISSUER}/protocol/openid-connect/token",
            "Discovery: falscher Token-Endpunkt",
        )
        print("student: Discovery korrekt, TLS-Zertifikat geprüft")
        for username in ("admin", "student"):
            check_user(client, secret, username)


if __name__ == "__main__":
    main()
