<!-- ABOUTME: Help documentation for the Gemini Vision ComfyUI node. -->
<!-- ABOUTME: Analyzes images using Gemini's multimodal vision capabilities. -->

# Gemini Vision

Analyzes images using Gemini's multimodal vision capabilities. Supports single images and batches for tasks like captioning, visual Q&A, and structured data extraction.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | - | Image(s) to analyze (supports batches) |
| prompt | String | "Describe this image in detail." | Question or instruction about the image(s) |
| client | GEMINI_API_CLIENT | - | Gemini API client (optional if API key is configured in Settings) |
| model | Combo | gemini-3.5-flash | Model to use: gemini-3.1-pro-preview, gemini-3.8-flash, gemini-3.7-flash, gemini-3.6-flash, gemini-3.5-flash, gemini-3.5-flash-lite (optional) |
| max_tokens | Int | 8192 | Maximum analysis length, 256-65536 (optional) |
| temperature | Float | 0.4 | Creativity level, lower=more factual, 0.0-2.0 (optional) |
| top_p | Float | 0.95 | Nucleus sampling threshold, 0.0=disabled (optional) |
| top_k | Int | 40 | Top-k sampling limit, 0=disabled (optional) |
| stop_sequences | String | "" | Stop generation at these sequences, one per line, max 5 (optional) |
| response_mime_type | Combo | default | Output format: default, text/plain, or application/json (optional) |
| response_schema | String | "" | JSON schema for structured output, used with application/json (optional) |
| thinking_level | Combo | none | Reasoning depth: none, minimal, low, medium, high. none sends no setting, so the model thinks at its own default level (it does not turn thinking off). minimal is raised to low on 3.1 Pro Preview, 3.7 Flash and 3.8 Flash, which reject it (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| analysis | String | Text analysis of the image(s) |

## Notes

- Default temperature is 0.4 (lower than text generation) for more factual analysis
- Use JSON mode (response_mime_type = application/json) to extract structured data from images like receipts or forms
- Batch images are all sent together in a single request
