"""Config flow for Smarter Climate integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (CONF_CLIMATE_ENTITY, CONF_HUMIDITY_SENSOR,
                    CONF_TARGET_HUMIDITY, CONF_TARGET_TEMPERATURE,
                    CONF_TEMPERATURE_SENSOR, DEFAULT_TARGET_HUMIDITY,
                    DEFAULT_TARGET_TEMPERATURE, DOMAIN)

_LOGGER = logging.getLogger(__name__)

def _get_schema():
    """Get the config flow schema."""
    return vol.Schema(
        {
            vol.Required(CONF_CLIMATE_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="climate")
            ),
            vol.Required(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
            ),
            vol.Required(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="humidity")
            ),
            vol.Optional(CONF_TARGET_TEMPERATURE, default=DEFAULT_TARGET_TEMPERATURE): selector.NumberSelector(
                selector.NumberSelectorConfig(min=18, max=30, step=0.5, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_TARGET_HUMIDITY, default=DEFAULT_TARGET_HUMIDITY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=50, max=70, step=1, mode=selector.NumberSelectorMode.BOX)
            ),
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
            # Create a unique ID based on the climate entity
            climate_entity = user_input[CONF_CLIMATE_ENTITY]
            await self.async_set_unique_id(climate_entity)
            self._abort_if_unique_id_configured()

            # Create a title based on the climate entity name
            return self.async_create_entry(
                title=f"Smarter Climate - {climate_entity}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_get_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguration of the integration."""
        errors: dict[str, str] = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        if entry is None:
            return self.async_abort(reason="not_found")

        if user_input is not None:
            # Create a unique ID based on the climate entity
            climate_entity = user_input[CONF_CLIMATE_ENTITY]
            # Ensure the unique ID matches the current entry's unique ID for reconfiguration
            await self.async_set_unique_id(climate_entity)
            self._abort_if_unique_id_mismatch(reason="wrong_climate_entity")

            # Validate that the entities exist (optional, but good practice for reconfigure)
            # This validation should ideally be in a shared helper function or validated in controller
            if not self.hass.states.get(user_input[CONF_CLIMATE_ENTITY]):
                errors[CONF_CLIMATE_ENTITY] = "entity_not_found"
            if not self.hass.states.get(user_input[CONF_TEMPERATURE_SENSOR]):
                errors[CONF_TEMPERATURE_SENSOR] = "entity_not_found"
            if not self.hass.states.get(user_input[CONF_HUMIDITY_SENSOR]):
                errors[CONF_HUMIDITY_SENSOR] = "entity_not_found"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )

        # Pre-fill the form with current values
        suggested_values = entry.data

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _get_schema(), suggested_values
            ),
            errors=errors,
        )
