<!-- ABOUTME: Help documentation for the WaveSpeed LTX 2.3 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates video clips from text prompts using Lightricks LTX 2.3 via WaveSpeed AI. -->

# WaveSpeed LTX 2.3 Text-to-Video

Generates video clips from text prompts using Lightricks' LTX 2.3 model via the WaveSpeed AI API. Returns a URL to the generated video.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the video to generate |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| resolution | Combo | 720p | Output resolution: 480p, 720p, or 1080p (optional) |
| aspect_ratio | Combo | 16:9 | Output aspect ratio: 16:9 or 9:16 (optional) |
| duration | Int | 5 | Video duration in seconds, 5 to 20 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **Distinct generation from LTX 2 Pro** — LTX 2.3 supports longer durations (up to 20s) and an explicit resolution knob, but does not emit synchronized audio.
- **Prompt is required** — must be non-empty
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
