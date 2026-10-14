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
| temperature | Float | 0.7 | Creativity level, 0.0–2.0 (optional). Sent only when `reasoning_effort` is `none` on gpt-6-sol, gpt-6-luna or a gpt-5.6 tier; dropped otherwise, since every model rejects it while reasoning |
| max_tokens | Int | 4096 | Maximum response length (optional). Range: 256–128000 |
| top_p | Float | 1.0 | Nucleus sampling threshold, 1.0=disabled (optional). Range: 0.0–1.0. Sent only when `reasoning_effort` is `none` on gpt-6-sol, gpt-6-luna or a gpt-5.6 tier; dropped otherwise, since every model rejects it while reasoning |
| stop_sequences | String | (empty) | Stop generation at these sequences, one per line (optional). Ignored by every current model, which rejects `stop` even with reasoning off; kept so saved workflows load |
| response_format | Combo | default | Output format: default, json_object (JSON mode) or json_schema (strict Structured Outputs, using the `json_schema` input) (optional) |
| reasoning_effort | Combo | default | Reasoning depth: default / none / minimal / low / medium / high / xhigh (optional). `default` sends nothing, so the model reasons at its own default (medium). `none` turns reasoning off on gpt-6-sol, gpt-6-luna and the gpt-5.6 tiers; gpt-6.1-sol and gpt-6-astra cannot turn it off, so there `none` acts like `default`. `minimal` is rejected by every current model and is sent as `low`. Dropped for chat-latest |
| verbosity | Combo | default | Output verbosity: default / low / medium / high (optional). Shapes how chatty the response is independent of max_tokens. Not sent to chat-latest, which accepts it but ignores it |
| seed | Int | -1 | Seed for reproducible outputs (best-effort). -1 randomizes every run (optional) |
| json_schema | String | (empty) | JSON Schema the reply must match when response_format is json_schema, sent with `strict: true` (optional). Strict mode needs every property in `required` and `additionalProperties: false` on each object. Empty, invalid or non-object JSON is refused before the request |

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
