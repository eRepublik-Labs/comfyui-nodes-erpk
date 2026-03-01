<!-- ABOUTME: Help documentation for the Qwen Image Edit Plus ComfyUI node. -->
<!-- ABOUTME: Advanced multi-reference image editing with up to 3 reference images. -->

# Qwen Image Edit Plus

Advanced image editing with multiple reference images. Accepts up to 3 reference images and supports bilingual (Chinese and English) text prompts.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Qwen Edit Plus | Model variant: Qwen Edit Plus or Qwen Edit 2511 (multi-person editing, improved consistency) |
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

- **Pricing:** $0.02 per image
- **API Docs:** [Qwen Image Edit Plus](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit-plus)
- Both prompt and images are required
- Maximum of 3 reference images; provide as comma-separated URLs
- Two model variants: **Qwen Edit Plus** (default) and **Qwen Edit 2511** (multi-person editing, improved consistency)
