"""Constants for the TIER integration."""
from typing import Final

DOMAIN: Final = "tier"

CONF_FILTER_NON_RENTABLE_VEHICLES: Final = "filter_non_rentable_vehicles"
CONF_MINIMUM_BATTERY_LEVEL: Final = "minimum_battery_level"

DEFAULT_FILTER_NON_RENTABLE_VEHICLES: Final = True
DEFAULT_MINIMUM_BATTERY_LEVEL: Final = 50
DEFAULT_RADIUS: Final = 250
DEFAULT_SCAN_INTERVAL: Final = 5

SENSOR_KEY_AVAILABLE_BICYCLES: Final = "available_bicycles"
SENSOR_KEY_AVAILABLE_MOPEDS: Final = "available_mopeds"
SENSOR_KEY_AVAILABLE_SCOOTERS: Final = "available_scooters"
