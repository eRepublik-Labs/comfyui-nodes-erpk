<!-- ABOUTME: Help documentation for the Kling 2.6 Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a starting image into a short video using Kling 2.6 Std and Pro models. -->

# Kling 2.6 Image-to-Video

Animates a starting image into a short video using Kling 2.6 models via the WaveSpeed AI API. The Pro variant additionally supports `cfg_scale`, an end-frame image, and joint audio-video co-generation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | - | Starting image as a ComfyUI IMAGE tensor (optional). Preferred — takes precedence over `image_url` when connected |
| end_image | IMAGE | - | Pro only: end-frame image as a ComfyUI IMAGE tensor (optional). Preferred — takes precedence over `end_image_url` when connected. Cannot be combined with `sound` |
| model | Combo | Kling 2.6 | Model variant: Kling 2.6 (Std) or Kling 2.6 Pro (adds cfg_scale, end_image, sound) |
| prompt | String | "" | Text description of scene motion, camera moves, and audio |
| image_url | String | "" | Starting image URL (JPG/JPEG/PNG, max 10MB, min 300px each side, aspect 1:2.5-2.5:1). Fallback when the IMAGE input is not connected |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| negative_prompt | String | "" | Elements to exclude from visuals and audio (optional) |
| duration | Combo | 5 | Video duration in seconds: 5 or 10 (optional) |
| end_image_url | String | "" | Pro only: end-frame URL (optional). Fallback when the `end_image` IMAGE input is not connected. Cannot be combined with `sound` |
| cfg_scale | Float | 0.5 | Pro only: guidance strength (0.3-0.8); higher follows the prompt more closely (optional) |
| sound | Boolean | True | Pro only: enable joint audio-video generation (doubles cost); cannot be combined with `end_image` (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **API endpoints:** `/api/v3/kwaivgi/kling-v2.6-std/image-to-video` (Std) and `/api/v3/kwaivgi/kling-v2.6-pro/image-to-video` (Pro)
- **Pro-only features:** `cfg_scale` (range 0.3-0.8), `end_image` / `end_image_url`, and `sound` — Std ignores these fields
- **Pro mutual exclusion:** `end_image` and `sound` cannot be used together — choose one
- **Required fields:** `prompt` and a starting image (IMAGE or `image_url`) — both must be non-empty
- **Dual input pattern:** every image field accepts either a ComfyUI IMAGE tensor (encoded as a base64 data URI) or a URL string; when both are provided the IMAGE input takes precedence
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
