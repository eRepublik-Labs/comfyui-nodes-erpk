<!-- ABOUTME: Help documentation for the Bytedance Seedream V4 ComfyUI node. -->
<!-- ABOUTME: Generates images from text prompts using ByteDance's Seedream V4 model. -->

# Bytedance Seedream V4

Generates high-quality images from text prompts using ByteDance's Seedream V4 model via the WaveSpeed AI API.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate |
| size_preset | Combo | "Custom" | Resolution preset (e.g. "1:1 2K (1408x1408)"). Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1408 | Custom width in pixels, 320-4096, step 8 (optional, only used when size_preset is "Custom") |
| height | Int | 1408 | Custom height in pixels, 320-4096, step 8 (optional, only used when size_preset is "Custom") |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** Standard
- **API Docs:** [Bytedance Seedream V4](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4)
- Width and height are ignored when a size preset other than "Custom" is selected
- Dimensions must be multiples of 8
