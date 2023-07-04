from __future__ import annotations

from hashlib import md5
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_SCAN_INTERVAL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
)
from homeassistant.data_entry_flow import FlowResult
from tier import TIER, NotFoundException, UnauthorizedException

import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL


class TIERConfigFlow(ConfigFlow, domain=DOMAIN):
    """The configuration flow for an TIER system."""

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Ask the user for an API token, site id, and a name for the system."""
        errors = {}
        if user_input:
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
                vol.Required(CONF_RADIUS): cv.positive_int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=config_schema, errors=errors
        )


def get_vehicles(api_token: str, latitude: float, longitude: float, radius: int):
    return TIER(api_token=api_token).vehicles.in_radius(latitude, longitude, radius)
