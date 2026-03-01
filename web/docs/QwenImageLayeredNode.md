<!-- ABOUTME: Help documentation for the Qwen Image Layered ComfyUI node. -->
<!-- ABOUTME: Decomposes images into 2-8 RGBA layers for compositing workflows. -->

# Qwen Image Layered

Decomposes a single image into 2-8 RGBA layers with transparency. Returns both RGB image layers and their corresponding alpha masks for use in compositing workflows.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | String | - | The image to decompose into layers (URL or path) |
| prompt | String | "" | Text description to guide layer decomposition (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| num_layers | Int | 4 | Number of layers to decompose into, 2-8 (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | IMAGE | RGB image layers (batch of N images) |
| masks | MASK | Alpha mask layers (batch of N masks) |

## Notes

- **Pricing:** $0.025 per layer
- **API Docs:** [Qwen Image Layered](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-layered)
- Image is required; prompt is optional
- Returns two outputs: RGB layers and their corresponding alpha masks
- Total cost depends on number of layers (e.g., 4 layers = $0.10)
