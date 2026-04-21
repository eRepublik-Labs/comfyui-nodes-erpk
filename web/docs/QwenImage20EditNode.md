<!-- ABOUTME: Help documentation for the Qwen Image 2.0 Edit ComfyUI node. -->
<!-- ABOUTME: Image editing with up to 3 reference images using Qwen Image 2.0 models. -->

# Qwen Image 2.0 Edit

Image editing with multiple reference images using Qwen Image 2.0 models. Accepts up to 3 reference images and supports bilingual (Chinese and English) text prompts.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Image 2.0 | Model variant: Qwen Image 2.0 (standard) or Qwen Image 2.0 Pro (higher quality) |
| prompt | String | "" | Text description of the desired image modifications (Chinese or English) |
| images | String | - | Reference images to edit, max 3 (comma-separated URLs or paths) |
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
| image | IMAGE | Edited image |

## Notes

- **API Docs:** [Qwen Image 2.0 Edit](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-2.0-edit)
- Both prompt and images are required
- Maximum of 3 reference images; provide as comma-separated URLs
- Two model variants: **Qwen Image 2.0** (standard, default) and **Qwen Image 2.0 Pro** (higher quality)
