"""Config flow for Smarter Climate integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

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
                selector.NumberSelectorConfig(min=5, max=50, step=0.5, mode=selector.NumberSelectorMode.BOX)
            ),
            vol.Optional(CONF_TARGET_HUMIDITY, default=DEFAULT_TARGET_HUMIDITY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
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

 