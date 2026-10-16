"""Tests for the TIER config and options flows."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests
from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from tier import UnauthorizedException

from custom_components.tier.const import (
    CONF_FILTER_NON_RENTABLE_VEHICLES,
    CONF_MINIMUM_BATTERY_LEVEL,
    DOMAIN,
)

USER_INPUT = {CONF_API_TOKEN: "token", CONF_LATITUDE: 51.5, CONF_LONGITUDE: -2.6}


async def test_user_flow(hass: HomeAssistant, mock_tier: MagicMock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "TIER (51.5, -2.6)"
    assert result["data"] == USER_INPUT


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (UnauthorizedException(), "invalid_auth"),
        (requests.ConnectionError(), "cannot_connect"),
        (ValueError(), "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant, mock_tier: MagicMock, side_effect: Exception, error: str
) -> None:
    mock_tier.vehicles.in_radius.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    # Recovers once the error clears.
    mock_tier.vehicles.in_radius.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_options_flow_reloads(
    hass: HomeAssistant, mock_tier: MagicMock, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 10,
            CONF_RADIUS: 500,
            CONF_MINIMUM_BATTERY_LEVEL: 0,
            CONF_FILTER_NON_RENTABLE_VEHICLES: False,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    mock_tier.vehicles.in_radius.assert_called_with(51.5, -2.6, 500)
    assert config_entry.runtime_data.update_interval.total_seconds() == 600
    assert hass.states.get("sensor.tier_51_5_2_6_available_scooters").state == "4"


async def test_reauth(
    hass: HomeAssistant, mock_tier: MagicMock, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "new"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_API_TOKEN] == "new"
