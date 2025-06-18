import logging

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.event import async_track_state_change
from homeassistant.const import (
    EVENT_HOMEASSISTANT_START,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    ATTR_TEMPERATURE,
)
from homeassistant.components.climate.const import (
    SERVICE_SET_TEMPERATURE,
    SERVICE_SET_HVAC_MODE,
    ATTR_TEMPERATURE as CLIMATE_ATTR_TEMPERATURE,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_DRY,
    HVAC_MODE_OFF,
)

_LOGGER = logging.getLogger(__name__)


class ThermostatController:
    """Manages the thermostat logic."""

    def __init__(
        self, hass, climate_entity_id, temperature_sensor_id, humidity_sensor_id, target_temperature, target_humidity
    ):
        """Initialize the controller."""
        self.hass = hass
        self._climate_entity_id = climate_entity_id
        self._temperature_sensor_id = temperature_sensor_id
        self._humidity_sensor_id = humidity_sensor_id
        self._target_temperature = target_temperature
        self._target_humidity = target_humidity

        self._current_temperature = None
        self._current_humidity = None

        _LOGGER.info(
            "ThermostatController initialized for climate: %s, temp: %s, hum: %s, target_temp: %s, target_hum: %s",
            self._climate_entity_id,
            self._temperature_sensor_id,
            self._humidity_sensor_id,
            self._target_temperature,
            self._target_humidity,
        )

    async def async_start(self):
        """Start tracking sensor changes."""
        async_track_state_change(
            self.hass,
            [self._temperature_sensor_id, self._humidity_sensor_id],
            self._async_sensor_state_listener,
        )

        # Also update on Home Assistant start in case sensors are already available
        self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_START, self._async_home_assistant_start_listener
        )

    async def _async_home_assistant_start_listener(self, _):
        """Handle Home Assistant start event."""
        _LOGGER.debug("Home Assistant started, checking initial sensor states.")
        await self._async_update_and_control()

    async def _async_sensor_state_listener(self, entity_id, old_state, new_state):
        """Handle sensor state changes."""
        if new_state is None or new_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            _LOGGER.debug("Sensor %s state is unknown or unavailable.", entity_id)
            return

        _LOGGER.debug("Sensor %s state changed from %s to %s", entity_id, old_state, new_state)

        if entity_id == self._temperature_sensor_id:
            try:
                self._current_temperature = float(new_state.state)
            except ValueError:
                _LOGGER.warning("Could not parse temperature from %s: %s", entity_id, new_state.state)
                self._current_temperature = None
        elif entity_id == self._humidity_sensor_id:
            try:
                self._current_humidity = float(new_state.state)
            except ValueError:
                _LOGGER.warning("Could not parse humidity from %s: %s", entity_id, new_state.state)
                self._current_humidity = None

        await self._async_update_and_control()

    async def _async_update_and_control(self):
        """Update internal states and control the climate entity."""
        if self._current_temperature is None or self._current_humidity is None:
            _LOGGER.debug("Current temperature or humidity not available, skipping climate control.")
            return

        _LOGGER.debug(
            "Controlling climate entity %s with current temp %s (target %s), current hum %s (target %s)",
            self._climate_entity_id,
            self._current_temperature,
            self._target_temperature,
            self._current_humidity,
            self._target_humidity,
        )

        # 1. 如果当前sensor读取的温度超过目标温度2度以上，则将climate模式改为cool模式，并将climate温度设置为目标温度
        if self._current_temperature > self._target_temperature + 2.0:
            _LOGGER.info(
                "Temperature (%s) is >2.0C above target (%s), setting mode to COOL and temp to %s",
                self._current_temperature,
                self._target_temperature,
                self._target_temperature,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_HVAC_MODE,
                {"entity_id": self._climate_entity_id, "hvac_mode": HVAC_MODE_COOL},
                blocking=False,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {"entity_id": self._climate_entity_id, CLIMATE_ATTR_TEMPERATURE: self._target_temperature},
                blocking=False,
            )
        # 2. 如果当前sensor读取的温度低于目标温度2度以上，则将climate模式改为heat模式，并将climate温度设置为目标温度
        elif self._current_temperature < self._target_temperature - 2.0:
            _LOGGER.info(
                "Temperature (%s) is <2.0C below target (%s), setting mode to HEAT and temp to %s",
                self._current_temperature,
                self._target_temperature,
                self._target_temperature,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_HVAC_MODE,
                {"entity_id": self._climate_entity_id, "hvac_mode": HVAC_MODE_HEAT},
                blocking=False,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {"entity_id": self._climate_entity_id, CLIMATE_ATTR_TEMPERATURE: self._target_temperature},
                blocking=False,
            )
        # 3. 如果当前湿度超过目标湿度10%， 则将climate模式改为除湿模式
        elif self._current_humidity > self._target_humidity + 10.0: # Check only if temperature conditions are not met
            _LOGGER.info(
                "Humidity (%s) is >10%% above target (%s), setting mode to DRY.",
                self._current_humidity,
                self._target_humidity,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_HVAC_MODE,
                {"entity_id": self._climate_entity_id, "hvac_mode": HVAC_MODE_DRY},
                blocking=False,
            )
        # 4. 如果以上条件都不满足，则默认设为cool模式，将将温度设置为目标温度
        else:
            _LOGGER.info(
                "No specific condition met, defaulting to COOL mode and temp to %s.",
                self._target_temperature,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_HVAC_MODE,
                {"entity_id": self._climate_entity_id, "hvac_mode": HVAC_MODE_COOL},
                blocking=False,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {"entity_id": self._climate_entity_id, CLIMATE_ATTR_TEMPERATURE: self._target_temperature},
                blocking=False,
            ) 