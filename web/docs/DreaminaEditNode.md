<!-- ABOUTME: Help documentation for the Bytedance Dreamina Edit ComfyUI node. -->
<!-- ABOUTME: Single-image editing using Dreamina V3.0 with text prompts. -->

# Bytedance Dreamina Edit

Edits a single image based on a text prompt using the ByteDance Dreamina V3.0 model.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired image modifications |
| image_url | String | - | URL of the image to edit |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1328 | Image width, 512-2048, step 8 (optional) |
| height | Int | 1328 | Image height, 512-2048, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Notes

- **Pricing:** $0.027 per image
- **API Docs:** [Dreamina V3.0 Edit](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-dreamina-v3-edit)
- Both prompt and image_url are required
- Use the WaveSpeed Upload Image node to get a URL for local images
