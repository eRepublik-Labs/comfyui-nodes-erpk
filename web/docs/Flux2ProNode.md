<!-- ABOUTME: Help documentation for the FLUX.2 Pro ComfyUI node. -->
<!-- ABOUTME: Text-to-image sized by width and height, with a seed sent to the API. -->

# FLUX.2 Pro

Generates an image from a text prompt with FLUX.2 Pro.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate |
| width | Int | 1024 | Output width, 256 to 2048 in steps of 16 |
| height | Int | 1024 | Output height, 256 to 2048 in steps of 16 |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| seed | Int | -1 | Sent to the API. -1 picks a random seed and generates again every run; a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** $0.03 per image
- **API Docs:** [FLUX.2 Pro Text-to-Image](https://wavespeed.ai/docs/docs-api/wavespeed-ai/flux-2-pro-text-to-image)
