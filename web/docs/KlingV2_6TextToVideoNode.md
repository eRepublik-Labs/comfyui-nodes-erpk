<!-- ABOUTME: Help documentation for the Kling 2.6 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates a short video from a text prompt using Kling 2.6 Std and Pro models. -->

# Kling 2.6 Text-to-Video

Generates a short video from a text prompt using Kling 2.6 models via the WaveSpeed AI API. The Pro variant additionally supports `cfg_scale` and joint audio-video co-generation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Kling 2.6 | Model variant: Kling 2.6 (Std) or Kling 2.6 Pro (adds cfg_scale, sound) |
| prompt | String | "" | Text description of the desired scene, motion, and audio |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| negative_prompt | String | "" | Elements to exclude from visuals and audio (optional) |
| aspect_ratio | Combo | 16:9 | Aspect ratio of the output video: 16:9, 9:16, or 1:1 (optional) |
| duration | Combo | 5 | Video duration in seconds: 5 or 10 (optional) |
| cfg_scale | Float | 0.5 | Pro only: guidance strength (0.0-1.0); higher follows the prompt more closely (optional) |
| sound | Boolean | True | Pro only: enable joint audio-video generation (doubles cost) (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **API endpoints:** `/api/v3/kwaivgi/kling-v2.6-std/text-to-video` (Std) and `/api/v3/kwaivgi/kling-v2.6-pro/text-to-video` (Pro)
- **Pro-only features:** `cfg_scale` (range 0.0-1.0) and `sound` — Std ignores these fields
- **Required fields:** `prompt` must be non-empty
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
