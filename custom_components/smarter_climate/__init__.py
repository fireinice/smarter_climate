"""The Smarter Climate integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

# Import config flow to ensure it's registered
from . import config_flow  # noqa: F401
from .const import (CONF_CLIMATE_ENTITY, CONF_HUMIDITY_SENSOR,
                    CONF_TARGET_HUMIDITY, CONF_TARGET_TEMPERATURE,
                    CONF_TEMPERATURE_SENSOR, DOMAIN)
from .controller import ThermostatController

_LOGGER = logging.getLogger(__name__)

@dataclass
class SmarterClimateData:
    """Runtime data for Smarter Climate integration."""
    controller: ThermostatController


# Type alias for config entry
SmarterClimateConfigEntry = ConfigEntry[SmarterClimateData]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Smarter Climate integration."""
    # No longer needed as we use config flow
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SmarterClimateConfigEntry) -> bool:
    """Set up Smarter Climate from a config entry."""
    _LOGGER.info("Setting up Smarter Climate integration for entry: %s", entry.title)

    # Extract configuration data
    climate_entity_id = entry.data[CONF_CLIMATE_ENTITY]
    temperature_sensor_id = entry.data[CONF_TEMPERATURE_SENSOR]
    humidity_sensor_id = entry.data[CONF_HUMIDITY_SENSOR]
    target_temperature = entry.data[CONF_TARGET_TEMPERATURE]
    target_humidity = entry.data[CONF_TARGET_HUMIDITY]

    # Create the controller
    controller = ThermostatController(
        hass,
        climate_entity_id,
        temperature_sensor_id,
        humidity_sensor_id,
        target_temperature,
        target_humidity,
    )

    # Store runtime data
    entry.runtime_data = SmarterClimateData(controller=controller)

    # Start the controller
    await controller.async_start()

    _LOGGER.info("Smarter Climate integration setup completed for entry: %s", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmarterClimateConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Smarter Climate integration for entry: %s", entry.title)
    
    # Cancel the periodic update if it's active
    if entry.runtime_data.controller._cancel_periodic_update:
        entry.runtime_data.controller._cancel_periodic_update()

    return True
