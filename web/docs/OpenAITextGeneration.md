<!-- ABOUTME: Help documentation for the OpenAI Text Generation ComfyUI node. -->
<!-- ABOUTME: Generates text using OpenAI models with configurable parameters. -->

# OpenAI Text Generation

General-purpose text generation using OpenAI models. Supports all GPT text models with configurable sampling parameters.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Text prompt for OpenAI |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-4o | Model to use. Options include gpt-5.2, gpt-5.1, gpt-4.1, gpt-4o, o3, and more (optional) |
| temperature | Float | 0.7 | Creativity level, 0.0=focused to 2.0=very creative (optional). Range: 0.0–2.0 |
| max_tokens | Int | 4096 | Maximum response length (optional). Range: 256–16384 |
| top_p | Float | 1.0 | Nucleus sampling threshold, 1.0=disabled (optional). Range: 0.0–1.0 |
| stop_sequences | String | (empty) | Stop generation at these sequences, one per line (optional) |
| response_format | Combo | default | Output format: default or json_object (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Generated text response |

## Notes

- Re-executes on every queue (not cached) since API responses vary
- Use json_object response format when you need structured JSON output
- Stop sequences are separated by newlines — each line is a separate stop string
