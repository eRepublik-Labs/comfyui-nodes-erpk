<!-- ABOUTME: Help documentation for the Gemini Text Generation ComfyUI node. -->
<!-- ABOUTME: Generates text using Gemini models with configurable sampling and output format. -->

# Gemini Text Generation

Generates text using Gemini models. Supports structured JSON output, thinking/reasoning modes, and configurable sampling parameters.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text prompt for Gemini |
| client | GEMINI_API_CLIENT | - | Gemini API client (optional if API key is configured in Settings) |
| model | Combo | gemini-3.5-flash | Model to use: gemini-3.1-pro-preview, gemini-3.5-flash, gemini-3-flash-preview, gemini-3.1-flash-lite, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite (optional) |
| temperature | Float | 0.7 | Creativity level, 0.0=focused to 2.0=very creative (optional) |
| max_tokens | Int | 8192 | Maximum response length, 256-65536 (optional) |
| top_p | Float | 0.95 | Nucleus sampling threshold, 0.0=disabled (optional) |
| top_k | Int | 40 | Top-k sampling limit, 0=disabled (optional) |
| stop_sequences | String | "" | Stop generation at these sequences, one per line, max 5 (optional) |
| response_mime_type | Combo | default | Output format: default, text/plain, or application/json (optional) |
| response_schema | String | "" | JSON schema for structured output, used with application/json (optional) |
| thinking_level | Combo | none | Reasoning depth: none, low, medium, high. Gemini 3+ only (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Generated text |

## Notes

- Set response_mime_type to "application/json" and provide a response_schema for structured data extraction
- Thinking levels increase output quality but use more tokens; only supported on Gemini 3+ models
- Set top_p to 0.0 or top_k to 0 to disable that sampling method
- Stop sequences are limited to 5 by the Gemini API
