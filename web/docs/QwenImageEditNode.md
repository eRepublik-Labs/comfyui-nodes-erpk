<!-- ABOUTME: Help documentation for the Qwen Image Edit ComfyUI node. -->
<!-- ABOUTME: Edits images using bilingual text prompts with semantic and appearance editing. -->

# Qwen Image Edit

Edits images based on text prompts. Supports both low-level visual appearance editing and high-level semantic editing with bilingual (Chinese and English) prompts.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired image modifications (Chinese or English) |
| image | String | - | The image to edit (URL or path) |
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
- **API Docs:** [Qwen Image Edit](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit)
- Both prompt and image are required
- Use the WaveSpeed Upload Image node to get a URL for local images
