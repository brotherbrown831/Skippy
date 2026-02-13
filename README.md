# Skippy

An AI personal assistant with long-term semantic memory, powered by Home Assistant, N8N, and PostgreSQL with pgvector. Named after the magnificently sarcastic AI from the Expeditionary Force book series.

## Architecture

```
                         ┌──────────────────┐
                         │   Input Channels  │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
            ┌───────▼───────┐           ┌───────▼───────┐
            │  HA Voice     │           │  OpenWebUI    │
            │  Pipeline     │           │  Chat         │
            └───────┬───────┘           └───────┬───────┘
                    │                           │
            ┌───────▼───────┐           ┌───────▼───────┐
            │  Conversation │           │  OpenAI Proxy │
            │  Memory Flow  │           │  Flow         │
            └───────┬───────┘           └───────┬───────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │     Shared Pipeline        │
                    │  1. Store user message     │
                    │  2. Retrieve memories      │
                    │  3. Get conversation history│
                    │  4. Build context + prompt  │
                    │  5. Call OpenAI LLM        │
                    │  6. Respond to user        │
                    │  7. Store assistant message │
                    │  8. Evaluate for new memory│
                    └───────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │       Data Layer           │
                    │  PostgreSQL + pgvector     │
                    │  ┌─────────────────────┐   │
                    │  │ conversations       │   │
                    │  │ messages            │   │
                    │  │ semantic_memories   │   │
                    │  └─────────────────────┘   │
                    └───────────────────────────┘
```

## Features

- **Voice assistant** via Home Assistant Wyoming satellites
- **Chat interface** via OpenWebUI (OpenAI-compatible proxy)
- **Long-term semantic memory** using pgvector embeddings
- **Automatic memory extraction** - LLM evaluates each conversation for facts worth remembering
- **Memory deduplication** - similar memories are reinforced rather than duplicated
- **Conversation persistence** - all messages stored in PostgreSQL
- **Sarcastic personality** inspired by Skippy from Expeditionary Force

## Infrastructure

- **Proxmox** - Hypervisor hosting all services in LXCs/VMs
- **Home Assistant** - Home automation + voice pipeline
- **N8N** - Workflow orchestration (all AI logic lives here)
- **PostgreSQL + pgvector** - Conversation storage + vector similarity search
- **OpenWebUI** - Local chat interface
- **OpenAI API** - LLM (gpt-4o-mini) + embeddings (text-embedding-3-small)

## N8N Workflows

There are 4 workflows that make up Skippy's brain:

### 1. Conversation Memory (`skippy_conversation_memory.json`)
The main voice pipeline workflow. Receives input from Home Assistant voice satellites via webhook.

**Flow:** Webhook → Store message → Retrieve memories + Get history (parallel) → Build context → Call OpenAI → Respond → Store response → Evaluate for memory

### 2. OpenAI Proxy (`skippy_openai_proxy.json`)
Exposes an OpenAI Chat Completions-compatible endpoint so OpenWebUI can talk to Skippy. Same pipeline as the voice workflow but accepts/returns OpenAI API format.

**Endpoint:** `POST /webhook/v1/chat/completions`

### 3. Memory Retriever (`skippy_memory_retriever.json`)
Called by the conversation workflows to find relevant memories. Embeds the query and performs cosine similarity search against stored memories in pgvector.

**Endpoint:** `POST /webhook/memory/retrieve`

### 4. Memory Evaluator (`skippy_memory_evaluator.json`)
Called after each conversation turn. An LLM decides if the exchange contains information worth remembering long-term. If so, it extracts and rewrites the fact, embeds it, checks for duplicates, and either stores a new memory or reinforces an existing one.

**Endpoint:** `POST /webhook/memory/evaluate`

**Memory categories:** `family`, `person`, `preference`, `project`, `technical`, `recurring_event`, `fact`

## Home Assistant Custom Component

The `custom_components/skippy` folder contains a Home Assistant integration that registers as a conversation agent, forwarding voice input to the N8N webhook.

### Installation

1. Copy `custom_components/skippy/` to your HA `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings > Devices & Services > Add Integration** and search for "Skippy"
4. Enter your N8N webhook URL
5. Set the conversation agent to "Skippy" in your voice pipeline

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `webhook_url` | N8N webhook URL | Required |
| `timeout` | Response timeout in seconds (5-120) | 30 |
| `agent_id` | Identifier for the assistant | "skippy" |

## Database Schema

```sql
-- Conversation tracking
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    updated_at TIMESTAMP
);

-- Message history
CREATE TABLE messages (
    conversation_id TEXT,
    role TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Semantic memory with vector embeddings
CREATE TABLE semantic_memories (
    memory_id SERIAL PRIMARY KEY,
    user_id TEXT,
    content TEXT,
    embedding vector,
    confidence_score FLOAT,
    reinforcement_count INT DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_from_conversation_id TEXT,
    category TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## License

MIT
