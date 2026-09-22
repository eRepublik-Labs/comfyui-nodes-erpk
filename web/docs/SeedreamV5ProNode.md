<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Pro ComfyUI node. -->
<!-- ABOUTME: Text-to-image sized by aspect ratio and a 1k/1.5k/2k resolution tier. -->

# Bytedance Seedream V5.0 Pro

Generates an image from a text prompt with ByteDance's Seedream V5.0 Pro. Unlike the earlier Seedream nodes, the size is set by an aspect ratio plus a resolution tier, not by width and height.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate |
| aspect_ratio | Combo | "1:1" | 1:1, 1:2, 2:1, 1:3, 3:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 9:21, 21:9 |
| resolution | Combo | "1k" | Output resolution tier: 1k, 1.5k or 2k |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| output_format | Combo | "jpeg" | jpeg or png (optional) |
| prompt_optimization_mode | Combo | "standard" | The model rewrites the prompt first. fast is several times quicker but follows long or intricate prompts less closely (optional) |
| enable_sync_mode | Boolean | false | Wait for result before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64 encoded output instead of URLs (optional) |
| seed | Int | -1 | Cache control only, not sent to the API. -1 generates again every run; a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image |

## Notes

- **Pricing:** $0.045 per image at 1k or 1.5k, $0.09 at 2k
- **API Docs:** [Bytedance Seedream V5.0 Pro](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v5.0-pro)
- The endpoint takes no seed, so the same prompt can give a different image each run
