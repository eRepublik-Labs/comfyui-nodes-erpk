<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Pro Edit ComfyUI node. -->
<!-- ABOUTME: Edits from up to 10 images, taken from an IMAGE batch or from URLs. -->

# Bytedance Seedream V5.0 Pro Edit

Edits images from a text prompt with ByteDance's Seedream V5.0 Pro, using up to 10 input images.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired modifications |
| images | Image | -- | Images to edit as an IMAGE batch, one image per slice, up to 10 (optional). Sent inline as base64, no upload. Takes precedence over image_url. Batched images must share one size, so combine different sizes through URLs |
| image_url | String | (empty) | Image URL(s) to edit, one per line or comma separated, up to 10. Needed unless images is connected |
| aspect_ratio | Combo | "auto" | auto follows the first image; otherwise one of 1:1, 1:2, 2:1, 1:3, 3:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 9:21, 21:9 |
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
| image | IMAGE | Edited image |

## Notes

- **Pricing:** $0.045 per image at 1k or 1.5k, $0.09 at 2k, plus $0.003 for each input image after the first
- **API Docs:** [Bytedance Seedream V5.0 Pro Edit](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v5.0-pro-edit)
- More than 10 input images is an error that names the count; nothing is dropped silently
