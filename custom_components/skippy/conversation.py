"""Conversation agent for Skippy N8N Assistant.

This agent forwards conversation queries to an N8N webhook
and returns the response to Home Assistant's voice pipeline.
"""

from __future__ import annotations

import logging
from typing import Literal

import aiohttp
from homeassistant.components import conversation
from homeassistant.components.conversation import ConversationInput, ConversationResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.util import ulid

from .const import (
    CONF_AGENT_ID,
    CONF_TIMEOUT,
    CONF_WEBHOOK_URL,
    DEFAULT_AGENT_ID,
    DEFAULT_TIMEOUT,
    DOMAIN,
    N8N_REQUEST_AGENT_ID,
    N8N_REQUEST_CONVERSATION_ID,
    N8N_REQUEST_LANGUAGE,
    N8N_REQUEST_TEXT,
    N8N_RESPONSE_ERROR,
    N8N_RESPONSE_TEXT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Skippy conversation agent from config entry."""
    agent = SkippyConversationAgent(hass, entry)
    conversation.async_set_agent(hass, entry, agent)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Skippy conversation agent."""
    conversation.async_unset_agent(hass, entry)
    return True


class SkippyConversationAgent(conversation.AbstractConversationAgent):
    """Skippy conversation agent that forwards to N8N."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self._webhook_url = entry.data[CONF_WEBHOOK_URL]
        self._timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self._agent_id = entry.data.get(CONF_AGENT_ID, DEFAULT_AGENT_ID)

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return "*"

    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        """Process a sentence and return a response."""
        conversation_id = user_input.conversation_id or ulid.ulid_now()

        # Prepare the payload for N8N
        payload = {
            N8N_REQUEST_TEXT: user_input.text,
            N8N_REQUEST_CONVERSATION_ID: conversation_id,
            N8N_REQUEST_LANGUAGE: user_input.language,
            N8N_REQUEST_AGENT_ID: self._agent_id,
        }

        _LOGGER.debug("Sending to N8N webhook: %s", payload)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._timeout),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        _LOGGER.error(
                            "N8N webhook returned status %s: %s",
                            response.status,
                            error_text,
                        )
                        return self._error_response(
                            f"N8N returned error status {response.status}",
                            conversation_id,
                        )

                    data = await response.json()
                    _LOGGER.debug("N8N response: %s", data)

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to connect to N8N webhook: %s", err)
            return self._error_response(
                "Failed to connect to N8N. Please check the webhook URL.",
                conversation_id,
            )
        except TimeoutError:
            _LOGGER.error("N8N webhook request timed out after %s seconds", self._timeout)
            return self._error_response(
                "N8N took too long to respond. Please try again.",
                conversation_id,
            )

        # Extract response text from N8N
        if N8N_RESPONSE_ERROR in data:
            return self._error_response(data[N8N_RESPONSE_ERROR], conversation_id)

        response_text = data.get(N8N_RESPONSE_TEXT, "")
        if not response_text:
            # Try common alternative response keys
            response_text = data.get("text") or data.get("message") or data.get("output") or ""

        if not response_text:
            _LOGGER.warning("N8N returned empty response: %s", data)
            response_text = "I received your message but got no response from N8N."

        # Build the response
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)

        return ConversationResult(
            response=intent_response,
            conversation_id=conversation_id,
        )

    def _error_response(
        self, error_message: str, conversation_id: str
    ) -> ConversationResult:
        """Build an error response."""
        intent_response = intent.IntentResponse(language="en")
        intent_response.async_set_error(
            intent.IntentResponseErrorCode.UNKNOWN,
            error_message,
        )
        return ConversationResult(
            response=intent_response,
            conversation_id=conversation_id,
        )
