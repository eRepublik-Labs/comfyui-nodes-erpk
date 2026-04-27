<!-- ABOUTME: Help documentation for the OpenAI Chat ComfyUI node. -->
<!-- ABOUTME: Multi-turn conversation with OpenAI models preserving message history. -->

# OpenAI Chat

Multi-turn conversation with OpenAI models. Preserves message history across turns by passing the chat session output back into the next node. Supports the full GPT-5.x family, GPT-4 family, and o-series reasoning models with configurable sampling, reasoning depth, and verbosity.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Your message in the conversation |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-5.5 | Model to use (optional). Options include gpt-5.5, gpt-5.5-pro, gpt-5.4 family, gpt-5.2, gpt-5.1, gpt-5, gpt-4.1, gpt-4o, o3, o4-mini |
| chat_session | OPENAI_CHAT_SESSION | — | Previous chat session to continue (optional). Connect from previous chat node |
| reset_conversation | Boolean | False | Start a new conversation, discarding history (optional) |
| temperature | Float | 0.7 | Creativity level, 0.0–2.0 (optional). Ignored by reasoning models |
| max_tokens | Int | 4096 | Maximum response length (optional). Range: 256–16384 |
| top_p | Float | 1.0 | Nucleus sampling threshold, 1.0=disabled (optional). Range: 0.0–1.0. Ignored by reasoning models |
| stop_sequences | String | (empty) | Stop generation at these sequences, one per line (optional). Ignored by reasoning models |
| response_format | Combo | default | Output format: default or json_object (optional) |
| reasoning_effort | Combo | none | Reasoning depth for reasoning-capable models: none / minimal / low / medium / high / xhigh (optional). Silently dropped for non-reasoning models |
| verbosity | Combo | default | Output verbosity for gpt-5.x models: default / low / medium / high (optional). Shapes how chatty the assistant is. Silently dropped for older models |
| seed | Int | -1 | Seed for reproducible outputs (best-effort). -1 randomizes every run (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Assistant's reply to your message |
| chat_session | OPENAI_CHAT_SESSION | Updated conversation history for chaining |

## Notes

- Chain multiple Chat nodes by connecting `chat_session` output to the next node's `chat_session` input
- Use `reset_conversation` to clear history and start fresh
- The chat session contains the full message history (user + assistant turns)
- `reasoning_effort` only applies to gpt-5.x reasoning models and o-series; other models silently drop it
- `verbosity` only applies to the gpt-5.x family; older families silently drop it. Use `low` for terse replies, `high` for detailed ones — independent of `max_tokens`
- `gpt-5.5` is the new default flagship. `gpt-5.5-pro` is the premium extended-compute tier (no streaming, $30/$180 per MTok)
