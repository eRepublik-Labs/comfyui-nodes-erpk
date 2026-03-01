<!-- ABOUTME: Help documentation for the JibMix Qwen Image ComfyUI node. -->
<!-- ABOUTME: Portrait-optimized text-to-image generation using JibMix Qwen model. -->

# JibMix Qwen Image

Portrait-optimized text-to-image generation using the JibMix Qwen model. Supports bilingual (Chinese and English) prompts.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
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

- **Pricing:** $0.02 per image
- **API Docs:** [JibMix Qwen Image](https://wavespeed.ai/docs/docs-api/wavespeed-ai/jib-mix-qwen-image-text-to-image)
- Prompt is required and cannot be empty
- Optimized for portrait and character generation
