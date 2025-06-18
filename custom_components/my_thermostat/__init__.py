import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.config_validation as cv

from .controller import ThermostatController

_LOGGER = logging.getLogger(__name__)

DOMAIN = "my_thermostat"

CONF_CLIMATE_ENTITY = "climate_entity_id"
CONF_TEMPERATURE_SENSOR = "temperature_sensor_id"
CONF_HUMIDITY_SENSOR = "humidity_sensor_id"
CONF_TARGET_TEMPERATURE = "target_temperature"
CONF_TARGET_HUMIDITY = "target_humidity"

DEFAULT_TARGET_TEMPERATURE = 22.0
DEFAULT_TARGET_HUMIDITY = 50.0

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIMATE_ENTITY): cv.entity_id,
                vol.Required(CONF_TEMPERATURE_SENSOR): cv.entity_id,
                vol.Required(CONF_HUMIDITY_SENSOR): cv.entity_id,
                vol.Optional(CONF_TARGET_TEMPERATURE, default=DEFAULT_TARGET_TEMPERATURE): vol.Coerce(float),
                vol.Optional(CONF_TARGET_HUMIDITY, default=DEFAULT_TARGET_HUMIDITY): vol.Coerce(float),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the My Thermostat integration."""
    _LOGGER.info("Setting up My Thermostat integration")

    if DOMAIN not in config:
        _LOGGER.error("Configuration for %s not found.", DOMAIN)
        return False

    domain_config = config[DOMAIN]

    climate_entity_id = domain_config[CONF_CLIMATE_ENTITY]
    temperature_sensor_id = domain_config[CONF_TEMPERATURE_SENSOR]
    humidity_sensor_id = domain_config[CONF_HUMIDITY_SENSOR]
    target_temperature = domain_config[CONF_TARGET_TEMPERATURE]
    target_humidity = domain_config[CONF_TARGET_HUMIDITY]

    controller = ThermostatController(
        hass,
        climate_entity_id,
        temperature_sensor_id,
        humidity_sensor_id,
        target_temperature,
        target_humidity,
    )

    hass.data[DOMAIN] = controller

    await controller.async_start()

    return True 