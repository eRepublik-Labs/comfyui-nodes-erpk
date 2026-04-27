<!-- ABOUTME: Help documentation for the OpenAI Text Generation ComfyUI node. -->
<!-- ABOUTME: Generates text using OpenAI models with configurable parameters. -->

# OpenAI Text Generation

General-purpose text generation using OpenAI models. Supports the full GPT-5.x family, GPT-4 family, and o-series reasoning models with configurable sampling, reasoning depth, and verbosity.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Text prompt for OpenAI |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-5.5 | Model to use. Options include gpt-5.5, gpt-5.5-pro, gpt-5.4 family, gpt-5.2, gpt-5.1, gpt-5, gpt-4.1, gpt-4o, o3, o4-mini and more (optional) |
| temperature | Float | 0.7 | Creativity level, 0.0=focused to 2.0=very creative (optional). Range: 0.0–2.0. Ignored by reasoning models (gpt-5.x reasoning + o-series) |
| max_tokens | Int | 4096 | Maximum response length (optional). Range: 256–16384. Sent as `max_completion_tokens` for newer models |
| top_p | Float | 1.0 | Nucleus sampling threshold, 1.0=disabled (optional). Range: 0.0–1.0. Ignored by reasoning models |
| stop_sequences | String | (empty) | Stop generation at these sequences, one per line (optional). Ignored by reasoning models |
| response_format | Combo | default | Output format: default or json_object (optional) |
| reasoning_effort | Combo | none | Reasoning depth for reasoning-capable models: none / minimal / low / medium / high / xhigh (optional). Silently dropped for non-reasoning models |
| verbosity | Combo | default | Output verbosity for gpt-5.x models: default / low / medium / high (optional). Shapes how chatty the response is independent of max_tokens. Silently dropped for older models that don't accept verbosity |
| seed | Int | -1 | Seed for reproducible outputs (best-effort). -1 randomizes every run (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Generated text response |

## Notes

- Re-executes on every queue (not cached) since API responses vary
- Use json_object response format when you need structured JSON output
- Stop sequences are separated by newlines — each line is a separate stop string
- `reasoning_effort` only applies to gpt-5.x reasoning models (5.5, 5.5-pro, 5.4 family) and o-series (o3, o3-mini, o3-pro, o4-mini). Other models silently drop it
- `verbosity` only applies to the gpt-5.x family (5.5, 5.5-pro, 5.4 family, 5.2 family, 5.1, 5/mini/nano). Older families silently drop it. Distinct from `max_tokens` — it shapes verbosity, not the hard length cap
- `gpt-5.5` is the new default flagship (1.05M context, $5/$30 per MTok). `gpt-5.5-pro` is the extended-compute premium tier ($30/$180 per MTok, no streaming)
