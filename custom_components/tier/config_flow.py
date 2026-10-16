"""Config flow for the TIER integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from hashlib import md5
from typing import Any

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import (
    CONF_API_TOKEN,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import HomeAssistant, callback
from tier import TIER, TIERException, UnauthorizedException

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

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
        vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS): cv.positive_int,
        vol.Required(
            CONF_MINIMUM_BATTERY_LEVEL, default=DEFAULT_MINIMUM_BATTERY_LEVEL
        ): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
        vol.Required(
            CONF_FILTER_NON_RENTABLE_VEHICLES,
            default=DEFAULT_FILTER_NON_RENTABLE_VEHICLES,
        ): cv.boolean,
    }
)


async def _async_validate(
    hass: HomeAssistant, api_token: str, latitude: float, longitude: float
) -> dict[str, str]:
    """Check the token works by searching around the location."""
    try:
        await hass.async_add_executor_job(
            TIER(api_token=api_token).vehicles.in_radius,
            latitude,
            longitude,
            DEFAULT_RADIUS,
        )
    except UnauthorizedException:
        return {"base": "invalid_auth"}
    except (TIERException, requests.RequestException):
        return {"base": "cannot_connect"}
    except Exception:
        _LOGGER.exception("Unexpected error validating the TIER API token")
        return {"base": "unknown"}
    return {}


def _location_unique_id(latitude: float, longitude: float) -> str:
    latitude_hash = md5(str(latitude).encode("utf-8")).hexdigest()
    longitude_hash = md5(str(longitude).encode("utf-8")).hexdigest()
    return f"tier_{latitude_hash}_{longitude_hash}"


class TIERConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for TIER."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for an API token and a location."""
        errors: dict[str, str] = {}
        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]

            await self.async_set_unique_id(_location_unique_id(latitude, longitude))
            self._abort_if_unique_id_configured()

            errors = await _async_validate(
                self.hass, user_input[CONF_API_TOKEN], latitude, longitude
            )
            if not errors:
                return self.async_create_entry(
                    title=f"TIER ({latitude}, {longitude})", data=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_TOKEN): cv.string,
                vol.Inclusive(
                    CONF_LATITUDE, "coordinates", default=self.hass.config.latitude
                ): cv.latitude,
                vol.Inclusive(
                    CONF_LONGITUDE, "coordinates", default=self.hass.config.longitude
                ): cv.longitude,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle a rejected API token."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new API token."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            errors = await _async_validate(
                self.hass,
                user_input[CONF_API_TOKEN],
                entry.data[CONF_LATITUDE],
                entry.data[CONF_LONGITUDE],
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_TOKEN: user_input[CONF_API_TOKEN]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): cv.string}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> TIEROptionsFlow:
        """Return the options flow."""
        return TIEROptionsFlow()


class TIEROptionsFlow(OptionsFlowWithReload):
    """Options for TIER."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
