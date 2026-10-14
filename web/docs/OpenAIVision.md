<!-- ABOUTME: Help documentation for the OpenAI Vision ComfyUI node. -->
<!-- ABOUTME: Analyzes images using OpenAI vision models. -->

# OpenAI Vision

Analyzes images using OpenAI's vision capabilities. Supports multiple images in a batch and configurable detail levels, plus reasoning depth and verbosity for the gpt-6.x and gpt-5.6 models.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Image(s) to analyze (ComfyUI tensor) |
| prompt | String | Describe this image in detail. | Question or instruction about the image(s) |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is in Settings) |
| model | Combo | gpt-6.1-sol | Vision model (optional). Options: gpt-6.1-sol, gpt-6-astra, gpt-6-sol, gpt-6-luna, gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, chat-latest |
| detail | Combo | auto | Image detail level: auto, low (faster/cheaper), high (more detailed) or original (full resolution) (optional). On gpt-6-astra and the gpt-5.6 tiers, auto already behaves as original |
| max_tokens | Int | 4096 | Maximum analysis length (optional). Range: 256–128000 |
| temperature | Float | 0.4 | Creativity level, lower=more factual (optional). Range: 0.0–2.0. Sent only when `reasoning_effort` is `none` on gpt-6-sol, gpt-6-luna or a gpt-5.6 tier; dropped otherwise, since every model rejects it while reasoning |
| reasoning_effort | Combo | default | Reasoning depth: default / none / minimal / low / medium / high / xhigh (optional). `default` sends nothing, so the model reasons at its own default (medium). `none` turns reasoning off on gpt-6-sol, gpt-6-luna and the gpt-5.6 tiers; gpt-6.1-sol and gpt-6-astra cannot turn it off, so there `none` acts like `default`. `minimal` is rejected by every current model and is sent as `low`. Dropped for chat-latest |
| verbosity | Combo | default | Output verbosity: default / low / medium / high (optional). Shapes how chatty the response is independent of max_tokens. Not sent to chat-latest, which accepts it but ignores it |
| seed | Int | -1 | Seed for reproducible outputs (best-effort). -1 randomizes every run (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| analysis | String | Text analysis of the image(s) |

## Notes

- Supports batch images — all images in the tensor are sent together as a multi-image vision request
- Use "low" detail for faster/cheaper analysis, "high" for fine-grained detail
- The temperature default of 0.4 is sent only with `reasoning_effort` none on gpt-6-sol, gpt-6-luna or a gpt-5.6 tier; every other case drops it
- `reasoning_effort` and `verbosity` apply to the gpt-6.x and gpt-5.6 models; chat-latest drops both
- `gpt-6.1-sol` is the default vision model (image input measured working 2026-10-01). Use `gpt-6-astra` for the most demanding analysis ($10/$50 per MTok)
