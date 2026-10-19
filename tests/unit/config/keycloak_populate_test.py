"""KeycloakPopulateService mit nachgebautem UserService und temporärer CSV prüfen."""

lazy from pathlib import Path
lazy from unittest.mock import Mock

import pytest
from keycloak import KeycloakConnectionError
lazy from pytest_mock import MockerFixture

from student.config.dev.keycloak_populate import (
    KeycloakPopulateService,
    keycloak_populate,
)
from student.security import Role, UserService

_CSV: str = (
    "id;version;matrikelnummer;nachname;vorname;email;username;erzeugt;aktualisiert\n"
    "1;0;123456;Mustermann;Max;max@h-ka.de;admin;2026-10-01;2026-10-01\n"
    "20;0;654321;Musterfrau;Erika;erika@h-ka.de;erika;2026-10-02;2026-10-02\n"
    "30;0;111111;Schmidt;Lena;lena@h-ka.de;lena;2026-10-03;2026-10-03\n"
)
"""Aufbau wie extras/compose/postgres/init/student/csv/student.csv."""


@pytest.fixture
def user_service(mocker: MockerFixture) -> Mock:
    """Attrappe für den UserService ohne Keycloak."""
    return mocker.Mock(spec=UserService)


@pytest.fixture
def csv_datei(mocker: MockerFixture, tmp_path: Path) -> Path:
    """Temporäre CSV-Datei mit admin und zwei Studierenden."""
    path = tmp_path / "student.csv"
    path.write_text(_CSV, encoding="utf-8")
    mocker.patch("student.config.dev.keycloak_populate.csv_config", str(path))
    return path


def test_populate(user_service: Mock, csv_datei: Path) -> None:  # ruff: ignore[unused-function-argument]
    """Alle außer admin werden gelöscht und mit Rolle student neu angelegt."""
    KeycloakPopulateService(user_service).populate()

    user_service.remove_all_users.assert_called_once()
    users = [call.args[0] for call in user_service.create_user.call_args_list]
    assert [user.username for user in users] == ["erika", "lena"]
    erika = users[0]
    assert erika.email == "erika@h-ka.de"
    assert erika.nachname == "Musterfrau"
    assert erika.vorname == "Erika"
    assert erika.roles == [Role.STUDENT]
    assert erika.password


def test_populate_ohne_csv(
    user_service: Mock, mocker: MockerFixture, tmp_path: Path
) -> None:
    """Fehlt die CSV-Datei, wird nur gelöscht und nichts angelegt."""
    mocker.patch(
        "student.config.dev.keycloak_populate.csv_config",
        str(tmp_path / "gibt-es-nicht.csv"),
    )

    KeycloakPopulateService(user_service).populate()

    user_service.remove_all_users.assert_called_once()
    user_service.create_user.assert_not_called()


def test_populate_ohne_keycloak(user_service: Mock, csv_datei: Path) -> None:  # ruff: ignore[unused-function-argument]
    """Ohne Keycloak-Verbindung bricht der Serverstart nicht ab."""
    user_service.remove_all_users.side_effect = KeycloakConnectionError

    KeycloakPopulateService(user_service).populate()

    user_service.create_user.assert_not_called()


@pytest.mark.parametrize("dev_modus", [True, False])
def test_keycloak_populate_nur_im_dev_modus(
    mocker: MockerFixture, *, dev_modus: bool
) -> None:
    """Neugeladen wird nur bei `[dev] keycloak-populate = true`."""
    mocker.patch(
        "student.config.dev.keycloak_populate.dev_keycloak_populate", dev_modus
    )
    factory = mocker.patch(
        "student.config.dev.keycloak_populate.get_keycloak_populate_service"
    )

    keycloak_populate()

    assert factory.return_value.populate.called is dev_modus
