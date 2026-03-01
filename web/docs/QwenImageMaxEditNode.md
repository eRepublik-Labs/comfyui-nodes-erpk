<!-- ABOUTME: Help documentation for the Qwen Image Max Edit ComfyUI node. -->
<!-- ABOUTME: Premium 20B multi-reference image editing with up to 6 reference images. -->

# Qwen Image Max Edit

Premium multi-reference image editing using the Qwen Image Max 20B model. Accepts up to 6 reference images with a simplified parameter set.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired image modifications |
| images | String | - | Reference images to edit, max 6 (comma-separated URLs or paths) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Notes

- **Pricing:** $0.07 per image
- **API Docs:** [Qwen Image Max Edit](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-max-edit)
- Both prompt and images are required
- Maximum of 6 reference images (more than other Qwen Edit nodes)
- Simplified parameter set: no output_format, sync_mode, or base64_output options
