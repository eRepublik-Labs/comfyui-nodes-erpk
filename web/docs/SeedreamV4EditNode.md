<!-- ABOUTME: Help documentation for the Bytedance Seedream V4 Edit ComfyUI node. -->
<!-- ABOUTME: Edits images based on text prompts using ByteDance's Seedream V4 Edit model. -->

# Bytedance Seedream V4 Edit

Edits images based on text prompts using ByteDance's Seedream V4 Edit model. Accepts up to 10 reference images.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the desired image modifications |
| image_url | String | -- | Image URL(s) to edit. Single URL or comma-separated. Max 10 images |
| size_preset | Combo | "Custom" | Resolution preset. Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1408 | Custom width in pixels, 320-4096, step 8 (optional) |
| height | Int | 1408 | Custom height in pixels, 320-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |
| enable_sync_mode | Boolean | false | Wait for result before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64 encoded output instead of URLs (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image |

## Notes

- **Pricing:** Standard
- **API Docs:** [Bytedance Seedream V4 Edit](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4-edit)
- Use the **WaveSpeed Upload Image** node to get image URLs from local images
- Accepts up to 10 reference images
