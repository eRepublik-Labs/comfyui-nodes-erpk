<!-- ABOUTME: Help documentation for the OpenAI Vision ComfyUI node. -->
<!-- ABOUTME: Analyzes images using OpenAI vision models. -->

# OpenAI Vision

Analyzes images using OpenAI's vision capabilities. Supports multiple images in a batch and configurable detail levels.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Image(s) to analyze (ComfyUI tensor) |
| prompt | String | Describe this image in detail. | Question or instruction about the image(s) |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-4o | Vision model. Options: gpt-5.2, gpt-5.1, gpt-5, gpt-4.1, gpt-4o, and more (optional) |
| detail | Combo | auto | Image detail level: auto, low (faster/cheaper), or high (more detailed) (optional) |
| max_tokens | Int | 4096 | Maximum analysis length (optional). Range: 256–16384 |
| temperature | Float | 0.4 | Creativity level, lower=more factual (optional). Range: 0.0–2.0 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| analysis | String | Text analysis of the image(s) |

## Notes

- Supports batch images — all images in the tensor are sent together
- Use "low" detail for faster/cheaper analysis, "high" for fine-grained detail
- Default temperature is 0.4 (lower than text generation) for more factual descriptions
