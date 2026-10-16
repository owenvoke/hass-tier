"""Data update coordinator for TIER."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from tier import TIER, TIERException, UnauthorizedException, Vehicle

from .const import (
    CONF_FILTER_NON_RENTABLE_VEHICLES,
    CONF_MINIMUM_BATTERY_LEVEL,
    DEFAULT_FILTER_NON_RENTABLE_VEHICLES,
    DEFAULT_MINIMUM_BATTERY_LEVEL,
    DEFAULT_RADIUS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30

type TIERConfigEntry = ConfigEntry[TIERUpdateCoordinator]


class TIERUpdateCoordinator(DataUpdateCoordinator[list[Vehicle]]):
    """Fetch the vehicles around a location."""

    config_entry: TIERConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: TIERConfigEntry) -> None:
        """Initialise the coordinator."""
        options = config_entry.options
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
            ),
        )
        self._tier = TIER(api_token=config_entry.data[CONF_API_TOKEN])
        self._latitude = float(config_entry.data[CONF_LATITUDE])
        self._longitude = float(config_entry.data[CONF_LONGITUDE])
        self._radius = int(options.get(CONF_RADIUS, DEFAULT_RADIUS))
        self._minimum_battery_level = int(
            options.get(CONF_MINIMUM_BATTERY_LEVEL, DEFAULT_MINIMUM_BATTERY_LEVEL)
        )
        self._filter_non_rentable_vehicles = bool(
            options.get(
                CONF_FILTER_NON_RENTABLE_VEHICLES, DEFAULT_FILTER_NON_RENTABLE_VEHICLES
            )
        )

    async def _async_update_data(self) -> list[Vehicle]:
        """Fetch the vehicles that pass the configured filters."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                vehicles = await self.hass.async_add_executor_job(
                    self._tier.vehicles.in_radius,
                    self._latitude,
                    self._longitude,
                    self._radius,
                )
        except UnauthorizedException as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except (TIERException, requests.RequestException, TimeoutError) as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err

        return [
            vehicle
            for vehicle in vehicles["data"]
            if not (
                self._filter_non_rentable_vehicles
                and vehicle["attributes"]["isRentable"] is False
            )
            and vehicle["attributes"]["batteryLevel"] >= self._minimum_battery_level
        ]
