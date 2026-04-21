<!-- ABOUTME: Help documentation for the Kling O3 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates a short video from a text prompt using Kling O3 models. -->

# Kling O3 Text-to-Video

Generates a short video from a text prompt using Kling O3 models via the WaveSpeed AI API.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Kling O3 | Model variant: Kling O3 (standard) or Kling O3 Pro (higher quality) |
| prompt | String | "" | Text description of the video to generate |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| duration | Int | 5 | Video duration in seconds, 3 to 10 (optional) |
| aspect_ratio | Combo | 16:9 | Aspect ratio of the output video (optional): 16:9, 9:16, 1:1 |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **API endpoints:** `/api/v3/kwaivgi/kling-video-o3-std/text-to-video` and `/api/v3/kwaivgi/kling-video-o3-pro/text-to-video`
- **Namespace:** Kling O3 lives under `kling-video-o3-*`, NOT `kling-v3.0-*` (which is the separate Kling 3.0 generation)
- **Prompt is required** — must be non-empty
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
