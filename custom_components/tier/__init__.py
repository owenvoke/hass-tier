"""The TIER integration"""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_API_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
)
from homeassistant.core import HomeAssistant

from .const import CONF_MINIMUM_BATTERY_LEVEL, DOMAIN, DEFAULT_SCAN_INTERVAL
from .coordinator import TIERUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    tier_coordinator = TIERUpdateCoordinator(
        hass=hass,
        name=config_entry.title,
        api_token=config_entry.data[CONF_API_TOKEN],
        latitude=config_entry.data[CONF_LATITUDE],
        longitude=config_entry.data[CONF_LONGITUDE],
        radius=config_entry.data[CONF_RADIUS],
        minimum_battery_level=config_entry.data[CONF_MINIMUM_BATTERY_LEVEL],
        update_interval=timedelta(
            minutes=(config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        ),
    )

    await tier_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = tier_coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data.pop(DOMAIN)

    return unload_ok
