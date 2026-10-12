"""Unit-Tests für den HealthRouter ohne laufende Datenbank."""

lazy from unittest.mock import Mock

import pytest
from sqlalchemy.exc import OperationalError
lazy from pytest_mock import MockerFixture

from student.router import liveness, readiness


@pytest.fixture
def engine_mock(mocker: MockerFixture) -> Mock:
    """Attrappe für die Engine im Modul health_router."""
    return mocker.patch("student.router.health_router.engine")


def test_liveness() -> None:
    """Die Liveness meldet immer, dass der Server läuft."""
    assert liveness() == {"status": "up"}


def test_readiness_db_up(engine_mock: Mock) -> None:
    """Die Readiness meldet eine erreichbare Datenbank."""
    connection = engine_mock.connect.return_value.__enter__.return_value
    connection.scalar.return_value = 1

    assert readiness() == {"db": "up"}


def test_readiness_db_down(engine_mock: Mock) -> None:
    """Die Readiness meldet eine nicht erreichbare Datenbank, statt abzustürzen."""
    engine_mock.connect.side_effect = OperationalError(
        statement="SELECT 1",
        params={},
        orig=ConnectionRefusedError("DB nicht erreichbar"),
    )

    assert readiness() == {"db": "down"}
