from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TIERUpdateCoordinator, DOMAIN
from .const import (
    SENSOR_KEY_AVAILABLE_SCOOTERS,
    SENSOR_KEY_AVAILABLE_MOPEDS,
    SENSOR_KEY_AVAILABLE_BICYCLES,
)


class TIERSensorEntity(CoordinatorEntity[TIERUpdateCoordinator], SensorEntity):
    """Representation of an TIER sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: TIERUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ):
        """Initialize the sensor and set the update coordinator."""
        super().__init__(coordinator)
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        self.entry = entry
        self.entity_description = description

    @property
    def native_value(self) -> str | int:
        if self.entity_description.key == SENSOR_KEY_AVAILABLE_BICYCLES:
            return sum(
                1
                for _ in filter(
                    lambda x: x.get("attributes").get("vehicleType") == "ebicycle",
                    self.coordinator.data.get("data"),
                )
            )

        if self.entity_description.key == SENSOR_KEY_AVAILABLE_MOPEDS:
            return sum(
                1
                for _ in filter(
                    lambda x: x.get("attributes").get("vehicleType") == "emoped",
                    self.coordinator.data.get("data"),
                )
            )

        if self.entity_description.key == SENSOR_KEY_AVAILABLE_SCOOTERS:
            return sum(
                1
                for _ in filter(
                    lambda x: x.get("attributes").get("vehicleType") == "escooter",
                    self.coordinator.data.get("data"),
                )
            )

        return STATE_UNAVAILABLE

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            name=self.coordinator.name,
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{self.entry.entry_id}")},
            manufacturer="TIER",
        )
