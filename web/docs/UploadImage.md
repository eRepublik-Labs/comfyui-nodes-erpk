<!-- ABOUTME: Help documentation for the WaveSpeed Upload Image ComfyUI node. -->
<!-- ABOUTME: Uploads images to WaveSpeed AI and returns temporary URLs for editing workflows. -->

# WaveSpeed Upload Image

Uploads image(s) to WaveSpeed AI and returns temporary URLs. Use this to prepare images for editing nodes that require image URLs.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | -- | Image(s) to upload to WaveSpeed AI |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| single_image_url | String | URL of the first uploaded image |
| all_image_urls | String | All uploaded image URLs (for batch processing) |

## Notes

- Uploaded URLs **expire after a short time** -- use them promptly in the same workflow
- Use `single_image_url` for nodes expecting one image, `all_image_urls` for batch processing
- Supports batch upload when multiple images are provided in the input tensor
