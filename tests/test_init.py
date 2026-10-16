"""Tests for TIER setup and sensors."""

from __future__ import annotations

from unittest.mock import MagicMock

import requests
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from tier import UnauthorizedException


async def test_sensors(
    hass: HomeAssistant, mock_tier: MagicMock, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    prefix = "sensor.tier_51_5_2_6"
    assert hass.states.get(f"{prefix}_available_scooters").state == "2"
    assert hass.states.get(f"{prefix}_available_bicycles").state == "1"
    assert hass.states.get(f"{prefix}_available_mopeds").state == "1"

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_on_network_error(
    hass: HomeAssistant, mock_tier: MagicMock, config_entry: MockConfigEntry
) -> None:
    mock_tier.vehicles.in_radius.side_effect = requests.ConnectionError()
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_auth_failure_starts_reauth(
    hass: HomeAssistant, mock_tier: MagicMock, config_entry: MockConfigEntry
) -> None:
    mock_tier.vehicles.in_radius.side_effect = UnauthorizedException()
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == ["reauth"]
