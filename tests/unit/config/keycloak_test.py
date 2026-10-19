"""Keycloak-Konfiguration ohne echte Secrets oder laufenden Server prüfen."""

import ssl
from runpy import run_path
from typing import Any
lazy from collections.abc import Callable
lazy from pathlib import Path

import pytest

import student.config.keycloak as keycloak_module
from student.config.config import app_config, resources_path
lazy from student.config.keycloak import KeycloakConfig


@pytest.fixture
def read_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Callable[[], KeycloakConfig]:
    """Modul isoliert mit temporärer .env und ohne echte Umgebung ausführen."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.setitem(app_config, "keycloak", {})

    def read() -> KeycloakConfig:
        return run_path(str(keycloak_module.__file__))["keycloak_config"]

    return read


def test_defaults(read_config: Callable[[], KeycloakConfig]) -> None:
    config = read_config()
    assert config.server_url == "https://localhost:8843/"
    assert config.realm_name == "student"
    assert config.client_id == "student-client"
    assert not config.client_secret_key
    assert config.verify == str(resources_path / "keycloak" / "certificate.crt")


@pytest.mark.parametrize("file_value", [None, "", "file-test-value"])
def test_secret_from_dotenv(
    read_config: Callable[[], KeycloakConfig], tmp_path: Path, file_value: str | None
) -> None:
    if file_value is not None:
        (tmp_path / ".env").write_text(f"CLIENT_SECRET={file_value}\n")
    config = read_config()
    assert config.client_secret_key == (file_value or "")
    assert "client_secret_key" not in repr(config)


def test_environment_has_priority(
    read_config: Callable[[], KeycloakConfig],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".env").write_text("CLIENT_SECRET=file-test-value\n")
    expected = "environment-test-value"
    monkeypatch.setenv("CLIENT_SECRET", expected)
    config = read_config()
    assert config.client_secret_key == expected
    assert expected not in repr(config)


def test_toml_settings(
    read_config: Callable[[], KeycloakConfig], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(
        app_config,
        "keycloak",
        {
            "schema": "https",
            "host": "keycloak",
            "port": 8443,
            "realm": "test-realm",
            "client-id": "test-client",
            "certificate": "test.crt",
        },
    )
    config = read_config()
    assert config.server_url == "https://keycloak:8443/"
    assert config.realm_name == "test-realm"
    assert config.client_id == "test-client"
    assert config.verify == str(resources_path / "keycloak" / "test.crt")


def test_certificate_is_usable(read_config: Callable[[], KeycloakConfig]) -> None:
    config = read_config()
    context = ssl.create_default_context(cafile=config.verify)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname


@pytest.fixture
def read_module(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Callable[[], dict[str, Any]]:
    """Wie `read_config`, liefert aber alle Konfigurationswerte des Moduls."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    monkeypatch.setitem(app_config, "keycloak", {})

    def read() -> dict[str, Any]:
        return run_path(str(keycloak_module.__file__))

    return read


def test_admin_defaults(read_module: Callable[[], dict[str, Any]]) -> None:
    """Die Admin-API nutzt Server, Realm und Client der OIDC-Konfiguration."""
    module = read_module()
    admin_config = module["keycloak_admin_config"]
    config = module["keycloak_config"]
    assert admin_config.username == "admin"
    assert not admin_config.password
    assert admin_config.server_url == config.server_url
    assert admin_config.realm_name == config.realm_name
    assert admin_config.client_id == config.client_id
    assert admin_config.verify == config.verify
    assert module["csv_config"] == (
        "extras/compose/postgres/init/student/csv/student.csv"
    )


def test_admin_toml_settings(
    read_module: Callable[[], dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Benutzer, Passwort und CSV-Datei kommen aus `[keycloak]` in app.toml."""
    password = "toml-test-value"  # ruff: ignore[hardcoded-password-string]
    monkeypatch.setitem(
        app_config,
        "keycloak",
        {"admin": "test-admin", "admin-password": password, "csv": "test.csv"},
    )
    module = read_module()
    admin_config = module["keycloak_admin_config"]
    assert admin_config.username == "test-admin"
    assert admin_config.password == password
    assert password not in repr(admin_config)
    assert module["csv_config"] == "test.csv"
