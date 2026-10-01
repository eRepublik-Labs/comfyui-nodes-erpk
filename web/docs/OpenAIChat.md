<!-- ABOUTME: Help documentation for the OpenAI Chat ComfyUI node. -->
<!-- ABOUTME: Multi-turn conversation with OpenAI models preserving message history. -->

# OpenAI Chat

Multi-turn conversation with OpenAI models. Preserves message history across turns by passing the chat session output back into the next node. Supports the GPT-6.x and GPT-5.6 reasoning tiers and chat-latest, with configurable reasoning depth and verbosity.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Your message in the conversation |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-6.1-sol | Model to use (optional). Options: gpt-6.1-sol, gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, chat-latest |
| chat_session | OPENAI_CHAT_SESSION | — | Previous chat session to continue (optional). Connect from previous chat node |
| reset_conversation | Boolean | False | Start a new conversation, discarding history (optional) |
| temperature | Float | 0.7 | Creativity level, 0.0–2.0 (optional). Ignored by every current model (each accepts only the default); kept so saved workflows load |
| max_tokens | Int | 4096 | Maximum response length (optional). Range: 256–128000 |
| top_p | Float | 1.0 | Nucleus sampling threshold, 1.0=disabled (optional). Range: 0.0–1.0. Ignored by every current model (each accepts only the default); kept so saved workflows load |
| stop_sequences | String | (empty) | Stop generation at these sequences, one per line (optional). Ignored by every current model (each accepts only the default); kept so saved workflows load |
| response_format | Combo | default | Output format: default or json_object (optional) |
| reasoning_effort | Combo | none | Reasoning depth: none / minimal / low / medium / high / xhigh (optional). `none` sends no effort, so the model uses its own default. `minimal` is rejected by every current model and is sent as `low`. Dropped for chat-latest |
| verbosity | Combo | default | Output verbosity: default / low / medium / high (optional). Shapes how chatty the response is independent of max_tokens. Dropped for chat-latest, which does not accept it |
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
- `reasoning_effort` and `verbosity` apply to the gpt-6.x and gpt-5.6 models; chat-latest drops both. Use `low` verbosity for terse replies, `high` for detailed ones — independent of `max_tokens`
- `gpt-6.1-sol` is the default ($2/$10 per MTok, 1.05M context, 128K output). `gpt-6-astra` is the top tier ($10/$50 per MTok)
- The gpt-5.5, gpt-5.4, gpt-5.2, gpt-5.1, gpt-5, gpt-4.1, gpt-4o and o-series models were removed on 2026-10-01
