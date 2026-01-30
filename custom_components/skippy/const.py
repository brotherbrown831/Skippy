"""Constants for Skippy N8N Assistant integration."""

DOMAIN = "skippy"

CONF_WEBHOOK_URL = "webhook_url"
CONF_TIMEOUT = "timeout"
CONF_AGENT_ID = "agent_id"

DEFAULT_TIMEOUT = 30
DEFAULT_AGENT_ID = "skippy"

# N8N webhook request/response keys
N8N_REQUEST_TEXT = "text"
N8N_REQUEST_CONVERSATION_ID = "conversation_id"
N8N_REQUEST_LANGUAGE = "language"
N8N_REQUEST_AGENT_ID = "agent_id"

N8N_RESPONSE_TEXT = "response"
N8N_RESPONSE_ERROR = "error"
