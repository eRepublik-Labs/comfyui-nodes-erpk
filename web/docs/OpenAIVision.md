<!-- ABOUTME: Help documentation for the OpenAI Vision ComfyUI node. -->
<!-- ABOUTME: Analyzes images using OpenAI vision models. -->

# OpenAI Vision

Analyzes images using OpenAI's vision capabilities. Supports multiple images in a batch and configurable detail levels, plus reasoning depth and verbosity for gpt-5.x models.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Image(s) to analyze (ComfyUI tensor) |
| prompt | String | Describe this image in detail. | Question or instruction about the image(s) |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-5.5 | Vision model. Options include gpt-5.5, gpt-5.5-pro, gpt-5.4 family, gpt-5.2, gpt-5.1, gpt-5, gpt-4.1, gpt-4o, gpt-4o-mini (optional) |
| detail | Combo | auto | Image detail level: auto, low (faster/cheaper), or high (more detailed) (optional) |
| max_tokens | Int | 4096 | Maximum analysis length (optional). Range: 256–16384 |
| temperature | Float | 0.4 | Creativity level, lower=more factual (optional). Range: 0.0–2.0 |
| reasoning_effort | Combo | none | Reasoning depth for reasoning-capable models: none / minimal / low / medium / high / xhigh (optional). Silently dropped for non-reasoning models |
| verbosity | Combo | default | Output verbosity for gpt-5.x models: default / low / medium / high (optional). Shapes how chatty the analysis is. Silently dropped for older models |
| seed | Int | -1 | Seed for reproducible outputs (best-effort). -1 randomizes every run (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| analysis | String | Text analysis of the image(s) |

## Notes

- Supports batch images — all images in the tensor are sent together as a multi-image vision request
- Use "low" detail for faster/cheaper analysis, "high" for fine-grained detail
- Default temperature is 0.4 (lower than text generation) for more factual descriptions
- O-series models (o3, o3-pro, etc.) are excluded from the vision dropdown — they don't support image input
- `reasoning_effort` only applies to gpt-5.x reasoning models and o-series; other models silently drop it
- `verbosity` only applies to the gpt-5.x family; older families silently drop it
- `gpt-5.5` is the new default vision model. Use `gpt-5.5-pro` for the most demanding analysis tasks (no streaming, $30/$180 per MTok)
