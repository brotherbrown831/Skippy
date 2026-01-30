"""Skippy N8N Assistant - Home Assistant Integration.

This integration provides a conversation agent that forwards
user queries to an N8N webhook for processing and returns
the response through Home Assistant's voice pipeline.
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from . import conversation as conversation_agent

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Skippy N8N Assistant from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register the conversation agent
    await conversation_agent.async_setup_entry(hass, entry)

    # Reload on config entry update
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    _LOGGER.info("Skippy N8N Assistant configured with webhook")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unregister the conversation agent
    await conversation_agent.async_unload_entry(hass, entry)

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
