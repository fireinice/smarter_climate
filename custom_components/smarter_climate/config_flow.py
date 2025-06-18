"""Config flow for Smarter Climate integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_CLIMATE_ENTITY,
    CONF_TEMPERATURE_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_TARGET_TEMPERATURE,
    CONF_TARGET_HUMIDITY,
    DEFAULT_TARGET_TEMPERATURE,
    DEFAULT_TARGET_HUMIDITY,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIMATE_ENTITY): cv.entity_id,
        vol.Required(CONF_TEMPERATURE_SENSOR): cv.entity_id,
        vol.Required(CONF_HUMIDITY_SENSOR): cv.entity_id,
        vol.Optional(CONF_TARGET_TEMPERATURE, default=DEFAULT_TARGET_TEMPERATURE): vol.Coerce(float),
        vol.Optional(CONF_TARGET_HUMIDITY, default=DEFAULT_TARGET_HUMIDITY): vol.Coerce(float),
    }
)


class SmarterClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smarter Climate."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate that the entities exist
            climate_entity = user_input[CONF_CLIMATE_ENTITY]
            temp_sensor = user_input[CONF_TEMPERATURE_SENSOR]
            humidity_sensor = user_input[CONF_HUMIDITY_SENSOR]

            # Check if entities exist
            if not self.hass.states.get(climate_entity):
                errors[CONF_CLIMATE_ENTITY] = "entity_not_found"
            if not self.hass.states.get(temp_sensor):
                errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
            if not self.hass.states.get(humidity_sensor):
                errors[CONF_HUMIDITY_SENSOR] = "entity_not_found"

            # Create a unique ID based on the climate entity
            await self.async_set_unique_id(climate_entity)
            self._abort_if_unique_id_configured()

            if not errors:
                # Create a title based on the climate entity name
                climate_state = self.hass.states.get(climate_entity)
                title = climate_state.attributes.get("friendly_name", climate_entity) if climate_state else climate_entity

                return self.async_create_entry(
                    title=f"Smarter Climate - {title}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate that the entities exist
            climate_entity = user_input[CONF_CLIMATE_ENTITY]
            temp_sensor = user_input[CONF_TEMPERATURE_SENSOR]
            humidity_sensor = user_input[CONF_HUMIDITY_SENSOR]

            # Check if entities exist
            if not self.hass.states.get(climate_entity):
                errors[CONF_CLIMATE_ENTITY] = "entity_not_found"
            if not self.hass.states.get(temp_sensor):
                errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
            if not self.hass.states.get(humidity_sensor):
                errors[CONF_HUMIDITY_SENSOR] = "entity_not_found"

            # Ensure the same climate entity is being used
            await self.async_set_unique_id(climate_entity)
            self._abort_if_unique_id_mismatch(reason="wrong_climate_entity")

            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )

        # Pre-fill the form with current values
        reconfigure_entry = self._get_reconfigure_entry()
        suggested_values = reconfigure_entry.data

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, suggested_values
            ),
            errors=errors,
        ) 