<!-- ABOUTME: Help documentation for the Bytedance Seedream V4 Edit Sequential ComfyUI node. -->
<!-- ABOUTME: Edits images with sequential generation for multiple coherent results. -->

# Bytedance Seedream V4 Edit Sequential

Edits images with sequential generation for multiple coherent results using ByteDance's Seedream V4 Edit Sequential model.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of desired modifications. The node automatically appends the image count |
| max_images | Int | 4 | Number of images to generate (1-15) |
| size_preset | Combo | "Custom" | Resolution preset. Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| image_url | String | (empty) | Image URL(s) to edit, one per line or comma separated, up to 10 (optional) |
| images | Image | -- | Images to edit as an IMAGE batch, one image per slice, up to 10 (optional). Sent inline as base64, no upload. Takes precedence over image_url. Batched images must share one size, so combine different sizes through URLs |
| width | Int | 1408 | Custom width in pixels, 320-4096, step 8 (optional) |
| height | Int | 1408 | Custom height in pixels, 320-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |
| enable_sync_mode | Boolean | false | Wait for result before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64 encoded output instead of URLs (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | IMAGE | Batch of edited images |

## Notes

- **Pricing:** $0.027/image
- **API Docs:** [Bytedance Seedream V4 Edit Sequential](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4-edit-sequential)
- Reference images are optional -- works as text-to-image when no images are provided
- The node automatically appends "Generate a set of N consecutive." to your prompt
