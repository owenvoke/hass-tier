"""Sensors for TIER."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    SENSOR_KEY_AVAILABLE_BICYCLES,
    SENSOR_KEY_AVAILABLE_MOPEDS,
    SENSOR_KEY_AVAILABLE_SCOOTERS,
)
from .coordinator import TIERConfigEntry
from .entity import TIERSensorEntity

PARALLEL_UPDATES = 0

VEHICLE_TYPES: dict[str, str] = {
    SENSOR_KEY_AVAILABLE_BICYCLES: "ebicycle",
    SENSOR_KEY_AVAILABLE_MOPEDS: "emoped",
    SENSOR_KEY_AVAILABLE_SCOOTERS: "escooter",
}

SENSORS: tuple[SensorEntityDescription, ...] = tuple(
    SensorEntityDescription(
        key=key, translation_key=key, state_class=SensorStateClass.MEASUREMENT
    )
    for key in VEHICLE_TYPES
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TIERConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    async_add_entities(
        TIERVehicleCountSensor(entry.runtime_data, entry, description)
        for description in SENSORS
    )


class TIERVehicleCountSensor(TIERSensorEntity):
    """The number of available vehicles of one type."""

    @property
    def native_value(self) -> int:
        """Return how many vehicles of this type are available."""
        vehicle_type = VEHICLE_TYPES[self.entity_description.key]
        return sum(
            1
            for vehicle in self.coordinator.data
            if vehicle["attributes"]["vehicleType"] == vehicle_type
        )
