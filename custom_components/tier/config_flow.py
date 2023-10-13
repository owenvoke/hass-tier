from __future__ import annotations

from datetime import timedelta
from hashlib import md5
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from tier import TIER, UnauthorizedException

import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_FILTER_NON_RENTABLE_VEHICLES,
    CONF_MINIMUM_BATTERY_LEVEL,
    DEFAULT_FILTER_NON_RENTABLE_VEHICLES,
    DEFAULT_MINIMUM_BATTERY_LEVEL,
    DEFAULT_RADIUS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class TIERConfigFlow(ConfigFlow, domain=DOMAIN):
    """The configuration flow for an TIER system."""

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Ask the user for an API token, site id, and a name for the system."""
        errors = {}
        if user_input is not None:
            try:
                vehicles = await self.hass.async_add_executor_job(
                    lambda: get_vehicles(
                        api_token=user_input[CONF_API_TOKEN],
                        latitude=user_input[CONF_LATITUDE],
                        longitude=user_input[CONF_LONGITUDE],
                        radius=user_input[CONF_RADIUS],
                    )
                )
                if vehicles:
                    # Make sure we're not configuring the same device
                    latitude_hash = md5(
                        str(user_input[CONF_LATITUDE]).encode("utf-8")
                    ).hexdigest()
                    longitude_hash = md5(
                        str(user_input[CONF_LONGITUDE]).encode("utf-8")
                    ).hexdigest()

                    await self.async_set_unique_id(
                        f"tier_{latitude_hash}_{longitude_hash}"
                    )
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=f"TIER ({user_input[CONF_LATITUDE]}, {user_input[CONF_LONGITUDE]})",
                        data=user_input,
                    )
            except UnauthorizedException:
                errors[CONF_API_TOKEN] = "invalid_api_token"
            else:
                errors[CONF_API_TOKEN] = "server_error"

        config_schema = vol.Schema(
            {
                vol.Required(CONF_API_TOKEN): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Inclusive(
                    CONF_LATITUDE, "coordinates", default=self.hass.config.latitude
                ): cv.latitude,
                vol.Inclusive(
                    CONF_LONGITUDE, "coordinates", default=self.hass.config.longitude
                ): cv.longitude,
                vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS): cv.positive_int,
                vol.Optional(
                    CONF_MINIMUM_BATTERY_LEVEL, default=DEFAULT_MINIMUM_BATTERY_LEVEL
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
                vol.Optional(
                    CONF_FILTER_NON_RENTABLE_VEHICLES,
                    default=DEFAULT_FILTER_NON_RENTABLE_VEHICLES,
                ): cv.boolean,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=config_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> TIEROptionsFlowHandler:
        return TIEROptionsFlowHandler(config_entry)


class TIEROptionsFlowHandler(OptionsFlow):
    """Config flow options handler for TIER."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry
        # Cast from MappingProxy to dict to allow update.
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            self.options.update(user_input)
            coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]

            update_interval = timedelta(
                seconds=self.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            )

            _LOGGER.debug("Updating coordinator, update_interval: %s", update_interval)

            coordinator.update_interval = update_interval

            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    vol.Required(
                        CONF_RADIUS,
                        default=self.config_entry.options.get(
                            CONF_RADIUS, DEFAULT_RADIUS
                        ),
                    ): cv.positive_int,
                    vol.Required(
                        CONF_FILTER_NON_RENTABLE_VEHICLES,
                        default=self.config_entry.options.get(
                            CONF_FILTER_NON_RENTABLE_VEHICLES,
                            DEFAULT_FILTER_NON_RENTABLE_VEHICLES,
                        ),
                    ): vol.Boolean(),
                }
            ),
        )


def get_vehicles(api_token: str, latitude: float, longitude: float, radius: int):
    return TIER(api_token=api_token).vehicles.in_radius(latitude, longitude, radius)
