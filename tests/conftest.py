"""Fixtures for TIER tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.const import CONF_API_TOKEN, CONF_LATITUDE, CONF_LONGITUDE
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tier.const import DOMAIN


def _vehicle(vehicle_type: str, battery: int, rentable: bool = True) -> dict:
    return {
        "attributes": {
            "vehicleType": vehicle_type,
            "batteryLevel": battery,
            "isRentable": rentable,
        }
    }


VEHICLES = {
    "data": [
        _vehicle("escooter", 90),
        _vehicle("escooter", 80),
        _vehicle("escooter", 10),  # below the default battery level
        _vehicle("escooter", 90, rentable=False),
        _vehicle("ebicycle", 60),
        _vehicle("emoped", 55),
    ]
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in every test."""
    yield


@pytest.fixture
def mock_tier() -> Generator[MagicMock]:
    """Patch the TIER client."""
    client = MagicMock()
    client.vehicles.in_radius.return_value = VEHICLES
    with (
        patch("custom_components.tier.config_flow.TIER", return_value=client),
        patch("custom_components.tier.coordinator.TIER", return_value=client),
    ):
        yield client


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A configured TIER entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="TIER (51.5, -2.6)",
        data={CONF_API_TOKEN: "token", CONF_LATITUDE: 51.5, CONF_LONGITUDE: -2.6},
    )
