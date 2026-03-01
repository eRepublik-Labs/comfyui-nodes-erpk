<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Lite ComfyUI node. -->
<!-- ABOUTME: Generates images at higher minimum resolution with enhanced typography. -->

# Bytedance Seedream V5.0 Lite

Generates images at higher minimum resolution (1440px) with enhanced typography using ByteDance's Seedream V5.0 Lite model. Same capabilities as V4.5 at a lower price point.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate |
| size_preset | Combo | "Custom" | Resolution preset (e.g. "1:1 (2048x2048)"). Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 2048 | Custom width in pixels, 1440-4096, step 8 (optional) |
| height | Int | 2048 | Custom height in pixels, 1440-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** $0.035/image
- **API Docs:** [Bytedance Seedream V5.0 Lite](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v5-0-lite)
- Higher minimum resolution (1440px) than V4.5 (1024px)
- Dimensions must be multiples of 8
