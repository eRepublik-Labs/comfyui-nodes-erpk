<!-- ABOUTME: Help documentation for the Qwen Image Max ComfyUI node. -->
<!-- ABOUTME: Premium 20B text-to-image generation with a simplified parameter set. -->

# Qwen Image Max

Premium text-to-image generation using the Qwen Image Max 20B model. Simplified interface with fewer output options compared to other Qwen nodes.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate (max 800 characters) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** $0.07 per image
- **API Docs:** [Qwen Image Max](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-max-text-to-image)
- Prompt is required (max 800 characters)
- Simplified parameter set: no output_format, sync_mode, or base64_output options
