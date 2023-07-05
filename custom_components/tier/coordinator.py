import logging
from datetime import timedelta

import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from tier import TIER, Vehicle, VehiclesCollection

_LOGGER = logging.getLogger(__name__)


class TIERUpdateCoordinator(DataUpdateCoordinator[Vehicle]):
    """Coordinates updates between all TIER sensors defined."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        api_token: str,
        latitude: str,
        longitude: str,
        radius: int,
        update_interval: timedelta,
    ) -> None:
        self._tier = TIER(api_token=api_token)
        self._latitude = latitude
        self._longitude = longitude
        self._radius = radius

        """Initialize the UpdateCoordinator for TIER sensors."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> VehiclesCollection:
        async with async_timeout.timeout(5):
            return await self.hass.async_add_executor_job(
                lambda: self._tier.vehicles.in_radius(
                    self._latitude, self._longitude, self._radius
                )
            )
