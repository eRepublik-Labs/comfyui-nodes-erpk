<!-- ABOUTME: Help documentation for the Bytedance Dreamina Text-to-Image ComfyUI node. -->
<!-- ABOUTME: Text-to-image generation using Dreamina V3.0 or V3.1 with optional prompt expansion. -->

# Bytedance Dreamina Text-to-Image

Generates images from text prompts using ByteDance Dreamina V3.0 or V3.1 models. Includes optional prompt expansion for enhanced results.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Dreamina V3.1 | Model variant: Dreamina V3.0 or Dreamina V3.1 |
| prompt | String | "" | Text description of the image to generate |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1328 | Image width, 512-2048, step 8 (optional) |
| height | Int | 1328 | Image height, 512-2048, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| enable_prompt_expansion | Boolean | true | Automatically expand and enhance the prompt for better results (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** $0.027 per image
- **API Docs:** [Dreamina V3.0](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-dreamina-v3-text-to-image) / [Dreamina V3.1](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-dreamina-v3-1-text-to-image)
- Prompt is required and cannot be empty
- Prompt expansion is enabled by default and enhances the prompt automatically
- Two model variants: **Dreamina V3.1** (default) and **Dreamina V3.0**
