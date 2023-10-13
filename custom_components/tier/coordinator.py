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
        minimum_battery_level: int,
        filter_non_rentable_vehicles: bool,
        update_interval: timedelta,
    ) -> None:
        self._tier = TIER(api_token=api_token)
        self._latitude = latitude
        self._longitude = longitude
        self._radius = radius
        self._minimum_battery_level = minimum_battery_level
        self._filter_non_rentable_vehicles = filter_non_rentable_vehicles

        """Initialize the UpdateCoordinator for TIER sensors."""
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> VehiclesCollection:
        async with async_timeout.timeout(5):
            vehicles: VehiclesCollection = await self.hass.async_add_executor_job(
                lambda: self._tier.vehicles.in_radius(
                    self._latitude, self._longitude, self._radius
                )
            )

            filtered_vehicles: list[Vehicle] = []

            for vehicle in vehicles["data"]:
                if (
                    self._filter_non_rentable_vehicles
                    and vehicle["attributes"]["isRentable"] is False
                ):
                    continue

                if vehicle["attributes"]["batteryLevel"] >= self._minimum_battery_level:
                    filtered_vehicles.append(vehicle)

            vehicles["data"] = filtered_vehicles

            return vehicles
