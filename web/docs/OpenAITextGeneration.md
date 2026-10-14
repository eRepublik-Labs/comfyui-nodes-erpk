<!-- ABOUTME: Help documentation for the OpenAI Text Generation ComfyUI node. -->
<!-- ABOUTME: Generates text using OpenAI models with configurable parameters. -->

# OpenAI Text Generation

General-purpose text generation using OpenAI models: the GPT-6.x and GPT-5.6 reasoning tiers and chat-latest, with configurable reasoning depth and verbosity.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Text prompt for OpenAI |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-6.1-sol | Model to use (optional). Options: gpt-6.1-sol, gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, chat-latest |
| temperature | Float | 0.7 | Creativity level, 0.0=focused to 2.0=very creative (optional). Range: 0.0–2.0. Sent only when `reasoning_effort` is `none` on gpt-6-sol, gpt-6-luna or a gpt-5.6 tier; dropped otherwise, since every model rejects it while reasoning |
| max_tokens | Int | 4096 | Maximum response length (optional). Range: 256–128000. Sent as `max_completion_tokens` |
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
| response | String | Generated text response |

## Notes

- Re-executes on every queue while seed is -1; a fixed seed reuses the cached result
- Use json_object response format when you need structured JSON output, or json_schema with a schema in `json_schema` to force its shape (measured working on every offered model on 2026-10-14)
- Stop sequences are separated by newlines — each line is a separate stop string (ignored by every current model)
- `reasoning_effort` and `verbosity` apply to the gpt-6.x and gpt-5.6 models; chat-latest is a non-reasoning model and drops both. `verbosity` is distinct from `max_tokens` — it shapes verbosity, not the hard length cap
- `gpt-6.1-sol` is the default: 1.05M context, 128K output, $2/$10 per MTok ($0.10 cached input). `gpt-6-astra` is the top tier ($10/$50); `gpt-6-luna` is the cheapest ($0.10/$0.50)
- Removed on 2026-10-01: gpt-5.5, gpt-5.5-pro, the gpt-5.4 family, gpt-5.2, gpt-5.2-pro, gpt-5.1, gpt-5/mini/nano, gpt-4.1 family, gpt-4o, gpt-4o-mini, o3, o3-mini, o3-pro, o4-mini. A saved workflow that names one fails validation until a current model is picked
