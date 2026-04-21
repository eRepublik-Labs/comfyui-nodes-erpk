<!-- ABOUTME: Help documentation for the Kling 3.0 Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a starting image into a short video using Kling 3.0 models. -->

# Kling 3.0 Image-to-Video

Animates a starting image into a short video using Kling 3.0 models via the WaveSpeed AI API. Accepts a text prompt describing the desired motion and an image URL as the starting frame.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Kling 3.0 | Model variant: Kling 3.0 (standard) or Kling 3.0 Pro (higher quality) |
| prompt | String | "" | Text description of the desired motion/scene |
| image | String | "" | URL of the starting image (use `WaveSpeed Upload Image` to produce one) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| duration | Int | 5 | Video duration in seconds, 3 to 10 (optional) |
| aspect_ratio | Combo | 16:9 | Aspect ratio of the output video (optional): 16:9, 9:16, 1:1 |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **API endpoints:** `/api/v3/kwaivgi/kling-v3.0-std/image-to-video` and `/api/v3/kwaivgi/kling-v3.0-pro/image-to-video`
- **Prompt and image are required** — both must be non-empty
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
