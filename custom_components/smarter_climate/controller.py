import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.event import async_track_state_change, async_track_time_interval
from homeassistant.const import (
    EVENT_HOMEASSISTANT_START,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    ATTR_TEMPERATURE,
)
from homeassistant.components.climate.const import (
    SERVICE_SET_TEMPERATURE,
    SERVICE_SET_HVAC_MODE,
    HVACMode,
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

        self._climate_was_off = True  # Tracks if climate was off
        self._cancel_periodic_update = None # Stores the function to cancel periodic updates

        _LOGGER.info(
            "ThermostatController initialized for climate: %s, temp: %s, hum: %s, target_temp: %s, target_hum: %s",
            self._climate_entity_id,
            self._temperature_sensor_id,
            self._humidity_sensor_id,
            self._target_temperature,
            self._target_humidity,
        )

    def _start_periodic_check(self) -> None:
        """Start the periodic update timer if not already active."""
        if self._cancel_periodic_update is None:
            _LOGGER.debug("Starting 15-minute periodic update for %s", self._climate_entity_id)
            self._cancel_periodic_update = async_track_time_interval(
                self.hass,
                self._async_update_and_control,
                timedelta(minutes=15),
            )

    def _stop_periodic_check(self) -> None:
        """Stop the periodic update timer if active."""
        if self._cancel_periodic_update:
            _LOGGER.debug("Stopping periodic update for %s", self._climate_entity_id)
            self._cancel_periodic_update()
            self._cancel_periodic_update = None

    async def async_start(self):
        """Start tracking sensor changes."""
        # Track climate entity state changes
        async_track_state_change(
            self.hass,
            self._climate_entity_id,
            self._async_climate_state_listener,
        )

        # Initial update on Home Assistant start
        self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_START, self._async_home_assistant_start_listener
        )

    async def _async_home_assistant_start_listener(self, _):
        """Handle Home Assistant start event."""
        _LOGGER.debug("Home Assistant started, checking initial climate state.")
        climate_state = self.hass.states.get(self._climate_entity_id)
        if climate_state and climate_state.state != HVACMode.OFF:
            _LOGGER.info("Climate entity %s is ON at startup. Triggering control and starting periodic check.", self._climate_entity_id)
            self._climate_was_off = False # Climate is on
            await self._async_update_and_control(None) # Perform initial check
            # Start periodic update
            self._start_periodic_check()
        else:
            self._climate_was_off = True # Climate is off or unavailable

    async def _async_climate_state_listener(self, entity_id, old_state, new_state):
        """Handle climate entity state changes."""
        if new_state is None or new_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            _LOGGER.debug("Climate entity %s state is unknown or unavailable.", entity_id)
            return

        _LOGGER.debug("Climate entity %s state changed from %s to %s", entity_id, old_state.state if old_state else "None", new_state.state)

        if old_state and old_state.state == HVACMode.OFF and new_state.state != HVACMode.OFF:
            # Climate turned on from off state
            _LOGGER.info("Climate entity %s turned on from OFF state. Triggering control logic and starting periodic check.", entity_id)
            self._climate_was_off = False
            await self._async_update_and_control(None)
            # Start periodic update
            self._start_periodic_check()
        elif new_state.state == HVACMode.OFF:
            # Climate turned off
            _LOGGER.info("Climate entity %s turned off. Cancelling periodic check and resetting _climate_was_off.", entity_id)
            self._stop_periodic_check()
            self._climate_was_off = True

    async def _async_update_and_control(self, _):
        """Update internal states and control the climate entity.
        This function is only called when climate turns on or Home Assistant starts.
        """
        # Fetch current sensor states directly
        temperature_state = self.hass.states.get(self._temperature_sensor_id)
        humidity_state = self.hass.states.get(self._humidity_sensor_id)

        current_temperature = None
        current_humidity = None

        if temperature_state and temperature_state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            try:
                current_temperature = float(temperature_state.state)
            except ValueError:
                _LOGGER.warning("Could not parse temperature from %s: %s", self._temperature_sensor_id, temperature_state.state)

        if humidity_state and humidity_state.state not in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            try:
                current_humidity = float(humidity_state.state)
            except ValueError:
                _LOGGER.warning("Could not parse humidity from %s: %s", self._humidity_sensor_id, humidity_state.state)

        if current_temperature is None or current_humidity is None:
            _LOGGER.debug("Current temperature or humidity not available, skipping climate control.")
            return

        _LOGGER.debug(
            "Controlling climate entity %s with current temp %s (target %s), current hum %s (target %s)",
            self._climate_entity_id,
            current_temperature,
            self._target_temperature,
            current_humidity,
            self._target_humidity,
        )

        # 1. 如果当前sensor读取的温度超过目标温度2度以上，则将climate模式改为cool模式，并将climate温度设置为目标温度
        if current_temperature > self._target_temperature + 2.0:
            _LOGGER.info(
                "Temperature (%s) is >2.0C above target (%s), setting mode to COOL and temp to %s",
                current_temperature,
                self._target_temperature,
                self._target_temperature,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_HVAC_MODE,
                {"entity_id": self._climate_entity_id, "hvac_mode": HVACMode.COOL},
                blocking=False,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {"entity_id": self._climate_entity_id, ATTR_TEMPERATURE: self._target_temperature},
                blocking=False,
            )
        # 2. 如果当前sensor读取的温度低于目标温度2度以上，则将climate模式改为heat模式，并将climate温度设置为目标温度
        elif current_temperature < self._target_temperature - 2.0:
            _LOGGER.info(
                "Temperature (%s) is <2.0C below target (%s), setting mode to HEAT and temp to %s",
                current_temperature,
                self._target_temperature,
                self._target_temperature,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_HVAC_MODE,
                {"entity_id": self._climate_entity_id, "hvac_mode": HVACMode.HEAT},
                blocking=False,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {"entity_id": self._climate_entity_id, ATTR_TEMPERATURE: self._target_temperature},
                blocking=False,
            )
        # 3. 如果当前湿度超过目标湿度10%， 则将climate模式改为除湿模式
        elif current_humidity > self._target_humidity + 10.0: # Check only if temperature conditions are not met
            _LOGGER.info(
                "Humidity (%s) is >10%% above target (%s), setting mode to DRY.",
                current_humidity,
                self._target_humidity,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_HVAC_MODE,
                {"entity_id": self._climate_entity_id, "hvac_mode": HVACMode.DRY},
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
                {"entity_id": self._climate_entity_id, "hvac_mode": HVACMode.COOL},
                blocking=False,
            )
            await self.hass.services.async_call(
                "climate",
                SERVICE_SET_TEMPERATURE,
                {"entity_id": self._climate_entity_id, ATTR_TEMPERATURE: self._target_temperature},
                blocking=False,
            ) 