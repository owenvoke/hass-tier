import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TIERUpdateCoordinator
from .entity import TIERSensorEntity
from .const import (
    SENSOR_KEY_AVAILABLE_SCOOTERS,
    SENSOR_KEY_AVAILABLE_MOPEDS,
    SENSOR_KEY_AVAILABLE_BICYCLES,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

SCAN_INTERVAL = timedelta(minutes=5)

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_KEY_AVAILABLE_BICYCLES,
        name="Available Bicycles",
        icon="mdi:bicycle",
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_AVAILABLE_MOPEDS,
        name="Available Mopeds",
        icon="mdi:moped",
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_AVAILABLE_SCOOTERS,
        name="Available Scooters",
        icon="mdi:scooter",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up all sensors for this entry."""
    coordinator: TIERUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        TIERSensorEntity(coordinator, entry, description) for description in SENSORS
    )
