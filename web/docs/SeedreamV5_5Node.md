<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.5 ComfyUI node. -->
<!-- ABOUTME: Text-to-image with a selectable background and an alpha mask output. -->

# Bytedance Seedream V5.5

Generates an image from a text prompt with ByteDance's Seedream V5.5. The size is set by an aspect ratio plus a resolution tier, and the background can be transparent.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the image to generate |
| aspect_ratio | Combo | "1:1" | 1:1, 1:2, 2:1, 1:3, 3:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 9:21, 21:9 |
| resolution | Combo | "1k" | Output resolution tier: 1k, 1.5k or 2k |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| output_format | Combo | "png" | jpeg or png (optional). A transparent background needs png |
| background | Combo | "auto" | auto, transparent or opaque (optional) |
| seed | Int | -1 | Cache control only, not sent to the API. -1 generates again every run; a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image, RGB |
| mask | MASK | The image's alpha: 1 where opaque, 0 where transparent. Same convention as the Layers nodes. ComfyUI's Load Image outputs the inverse, so add Invert Mask before a node that expects its convention |

## Notes

- **Pricing:** $0.02 per image at 1k or 1.5k, $0.035 at 2k
- **API Docs:** [Bytedance Seedream V5.5](https://wavespeed.ai/docs/docs-api/bytedance/seedream-v5.5)
- The endpoint takes no seed, so the same prompt can give a different image each run
- `background` transparent with `output_format` jpeg is an error before anything is billed, because JPEG cannot hold transparency
