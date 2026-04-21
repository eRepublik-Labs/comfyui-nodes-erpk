<!-- ABOUTME: Help documentation for the Qwen Image 2.0 Text-to-Image ComfyUI node. -->
<!-- ABOUTME: Generates images from bilingual text prompts using Qwen Image 2.0 models. -->

# Qwen Image 2.0 Text-to-Image

Generates high-quality images from text prompts using Qwen Image 2.0 models. Supports bilingual (Chinese and English) prompts.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Image 2.0 | Model variant: Qwen Image 2.0 (standard) or Qwen Image 2.0 Pro (higher quality) |
| prompt | String | "" | Text description of the image to generate (Chinese or English) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| output_format | Combo | jpeg | Output image format: jpeg, png, webp (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **API Docs:** [Qwen Image 2.0 Text-to-Image](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-2.0-text-to-image)
- Prompt is required and cannot be empty
- Two model variants available: **Qwen Image 2.0** (standard, default) and **Qwen Image 2.0 Pro** (higher quality)
