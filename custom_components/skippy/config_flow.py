"""Config flow for Skippy N8N Assistant integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_AGENT_ID,
    CONF_TIMEOUT,
    CONF_WEBHOOK_URL,
    DEFAULT_AGENT_ID,
    DEFAULT_TIMEOUT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_WEBHOOK_URL): str,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=120)
        ),
        vol.Optional(CONF_AGENT_ID, default=DEFAULT_AGENT_ID): str,
    }
)


async def validate_webhook(hass: HomeAssistant, webhook_url: str) -> bool:
    """Validate the webhook URL is reachable.

    We do a simple OPTIONS or HEAD request to verify connectivity.
    N8N webhooks might not respond to GET, so we just check connectivity.
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Try a POST with a test payload
            async with session.post(
                webhook_url,
                json={"text": "ping", "test": True},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                # N8N might return various status codes, but if we get a response
                # (even an error), the webhook is reachable
                _LOGGER.debug(
                    "Webhook validation response: %s", response.status
                )
                return True
    except aiohttp.ClientError as err:
        _LOGGER.error("Failed to validate webhook URL: %s", err)
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.error("Unexpected error validating webhook: %s", err)
        raise CannotConnect from err


class SkippyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Skippy N8N Assistant."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_webhook(self.hass, user_input[CONF_WEBHOOK_URL])
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on the webhook URL
                await self.async_set_unique_id(user_input[CONF_WEBHOOK_URL])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Skippy ({user_input.get(CONF_AGENT_ID, DEFAULT_AGENT_ID)})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
