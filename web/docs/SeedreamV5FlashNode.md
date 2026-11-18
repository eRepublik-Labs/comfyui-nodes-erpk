<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Flash ComfyUI node. -->
<!-- ABOUTME: Text-to-image sized by aspect ratio and a resolution tier, at a flat price. -->

# Bytedance Seedream V5.0 Flash

Generates an image from a text prompt with ByteDance's Seedream V5.0 Flash. The size is set by an aspect ratio plus a resolution tier, and every tier costs the same.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate |
| aspect_ratio | Combo | "1:1" | 1:1, 1:2, 2:1, 1:3, 3:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 9:21, 21:9 |
| resolution | Combo | "1k" | Output resolution tier: 1k, 1.5k or 2k |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| output_format | Combo | "jpeg" | jpeg or png (optional) |
| seed | Int | -1 | Cache control only, not sent to the API. -1 generates again every run; a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** $0.027 per image at every resolution tier
- **API Docs:** [Bytedance Seedream V5.0 Flash](https://wavespeed.ai/docs/docs-api/bytedance/seedream-v5.0-flash)
- The endpoint takes no seed, so the same prompt can give a different image each run
