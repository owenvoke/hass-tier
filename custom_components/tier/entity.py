"""Base entity for TIER."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TIERConfigEntry, TIERUpdateCoordinator


class TIERSensorEntity(CoordinatorEntity[TIERUpdateCoordinator], SensorEntity):
    """A TIER sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TIERUpdateCoordinator,
        entry: TIERConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="TIER",
        )
