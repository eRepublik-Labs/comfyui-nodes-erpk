<!-- ABOUTME: Help documentation for the Kling Elements ComfyUI node. -->
<!-- ABOUTME: Creates a reusable Kling element (character/style/scene anchor) for visual consistency across generations. -->

# Kling Elements

Creates a Kling element (a consistent character/style/scene anchor) via the WaveSpeed AI API and returns its element ID. Reference the returned ID from Pro-variant Kling i2v/t2v nodes through their `element_list` JSON-array input to preserve visual continuity across scenes.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| name | String | "" | Element name (max 20 characters) |
| description | String | "" | Element description (max 100 characters) |
| image | IMAGE | - | Front reference image as a ComfyUI IMAGE tensor (optional). Preferred — takes precedence over `image_url` when connected. Source should be ≥300px and ≤10MB after encoding |
| image_url | String | "" | Front reference image URL (optional). Fallback when the IMAGE input is not connected |
| element_refer_images | IMAGE | - | Batched IMAGE tensor of 1-3 additional reference images (optional). Preferred over `element_refer_url_list` when connected |
| element_refer_url_list | String | "" | JSON array of 1-3 additional reference image URLs (optional). Used only when `element_refer_images` is not connected |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| voice_id | String | "" | Bind an existing voice/tone to this element (optional) |
| tag_list | String | "" | JSON array of tags for organizing the element (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| element_id | STRING | The created element ID — pass into the `element_list` JSON array of Pro-variant Kling i2v/t2v nodes |

## Notes

- **API endpoint:** `/api/v3/kwaivgi/kling-elements`
- **Required fields:** `name`, `description`, the front reference image (IMAGE or `image_url`), and at least one additional reference image (1-3 via `element_refer_images` or `element_refer_url_list`)
- **Dual input pattern:** every image field accepts either a ComfyUI IMAGE tensor (encoded as a base64 data URI) or a URL string; when both are provided the IMAGE input takes precedence
- Element creation is short-running compared to video generation (polling interval 5s, 5-minute timeout)
- Consume the returned `element_id` from a Pro variant's `element_list` JSON array, e.g. `["elem_abc123"]`
