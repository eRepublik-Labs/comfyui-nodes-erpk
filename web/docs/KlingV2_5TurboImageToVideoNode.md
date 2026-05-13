<!-- ABOUTME: Help documentation for the Kling 2.5 Turbo Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a starting image into a short video using Kling 2.5 Turbo Std and Pro models. -->

# Kling 2.5 Turbo Image-to-Video

Animates a starting image into a short video using Kling 2.5 Turbo models via the WaveSpeed AI API. The Pro variant additionally supports an optional end-frame (`last_image`) for keyframe interpolation between two reference frames.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | - | Starting image as a ComfyUI IMAGE tensor (optional). Preferred — takes precedence over `image_url` when connected |
| last_image | IMAGE | - | Pro only: end-frame image as a ComfyUI IMAGE tensor for keyframe interpolation (optional). Preferred — takes precedence over `last_image_url` when connected |
| model | Combo | Kling 2.5 Turbo | Model variant: Kling 2.5 Turbo (Std) or Kling 2.5 Turbo Pro (higher quality, supports last_image) |
| prompt | String | "" | Text description of the desired motion/scene (max 2500 chars) |
| image_url | String | "" | Starting image URL (JPG/JPEG/PNG, min 300x300, aspect 1:2.5-2.5:1). Fallback when the IMAGE input is not connected |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| negative_prompt | String | "" | Elements to suppress or avoid in the generated video (optional) |
| guidance_scale | Float | 0.5 | Prompt adherence (0.0-1.0); higher values reduce creative deviation (optional) |
| duration | Combo | 5 | Video duration in seconds: 5 or 10 (optional) |
| last_image_url | String | "" | Pro only: end-frame URL for keyframe interpolation (optional). Fallback when the `last_image` IMAGE input is not connected |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **API endpoints:** `/api/v3/kwaivgi/kling-v2.5-turbo-std/image-to-video` (Std) and `/api/v3/kwaivgi/kling-v2.5-turbo-pro/image-to-video` (Pro)
- **Pro-only features:** `last_image` / `last_image_url` for keyframe interpolation — Std ignores these fields
- **Required fields:** `prompt` and a starting image (IMAGE or `image_url`) — both must be non-empty
- **Dual input pattern:** every image field accepts either a ComfyUI IMAGE tensor (encoded as a base64 data URI) or a URL string; when both are provided the IMAGE input takes precedence
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
