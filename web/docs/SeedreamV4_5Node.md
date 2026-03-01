<!-- ABOUTME: Help documentation for the Bytedance Seedream V4.5 ComfyUI node. -->
<!-- ABOUTME: Generates images with enhanced typography and text rendering using Seedream V4.5. -->

# Bytedance Seedream V4.5

Generates images with enhanced typography and text rendering using ByteDance's Seedream V4.5 model. Optimized for posters, logos, UI, and marketing layouts.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate |
| size_preset | Combo | "Custom" | Resolution preset (e.g. "1:1 (2048x2048)"). Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 2048 | Custom width in pixels, 1024-4096, step 8 (optional) |
| height | Int | 2048 | Custom height in pixels, 1024-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** Standard
- **API Docs:** [Bytedance Seedream V4.5](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4-5)
- Higher minimum resolution (1024px) than V4 (320px) for better text quality
- Dimensions must be multiples of 8
