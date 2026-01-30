# Skippy

A Home Assistant custom integration that connects Wyoming voice satellites to N8N workflows via webhooks, enabling AI-powered voice conversations.

## Architecture

```
Wyoming Satellite → Wake Word/STT → Home Assistant → Webhook → N8N Agent → Response → HA → TTS → Satellite
```

## Features

- Custom conversation agent for Home Assistant
- Forwards voice queries to N8N via webhooks
- Works with Wyoming protocol voice satellites
- Configurable timeout and agent ID
- Supports any N8N workflow with AI/LLM integration

## Installation

### 1. Install the Custom Component

Copy the `custom_components/skippy` folder to your Home Assistant `config/custom_components/` directory:

```
config/
└── custom_components/
    └── skippy/
        ├── __init__.py
        ├── config_flow.py
        ├── const.py
        ├── conversation.py
        ├── manifest.json
        ├── strings.json
        └── translations/
            └── en.json
```

Restart Home Assistant.

### 2. Set Up N8N Workflow

Import one of the workflow templates from the `n8n/` folder:

- `skippy_echo_test.json` - Simple echo test to verify connectivity
- `skippy_workflow_template.json` - Template with AI agent placeholder

After importing:
1. Activate the workflow in N8N
2. Copy the webhook URL (e.g., `https://your-n8n.com/webhook/skippy`)

### 3. Configure the Integration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Skippy"
3. Enter your N8N webhook URL
4. Optionally adjust timeout (default: 30 seconds)
5. Optionally set an agent ID (default: "skippy")

### 4. Configure Voice Pipeline

1. Go to **Settings → Voice Assistants**
2. Create or edit a voice pipeline
3. Set **Conversation Agent** to "Skippy"
4. Assign this pipeline to your Wyoming satellite

## N8N Webhook Format

### Request (from Home Assistant)

```json
{
  "text": "What's the weather like?",
  "conversation_id": "01HQXYZ...",
  "language": "en",
  "agent_id": "skippy"
}
```

### Response (to Home Assistant)

```json
{
  "response": "The weather is sunny with a high of 72 degrees."
}
```

The integration also checks for alternative keys: `text`, `message`, `output`.

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `webhook_url` | N8N webhook URL | Required |
| `timeout` | Response timeout in seconds (5-120) | 30 |
| `agent_id` | Identifier for the assistant | "skippy" |

## Troubleshooting

### "Failed to connect to N8N webhook"
- Verify N8N is running and accessible from Home Assistant
- Check the webhook URL is correct
- Ensure the workflow is activated in N8N

### "N8N took too long to respond"
- Increase the timeout in the integration settings
- Check N8N workflow performance
- Verify your AI/LLM service is responding

### Empty responses
- Check N8N workflow returns `response` key in JSON
- Review N8N execution logs for errors

## Development

This is an MVP prototype. Future enhancements could include:
- Conversation history/memory
- Multiple agent support
- Home Assistant entity control via N8N
- Custom wake word responses

## License

MIT
