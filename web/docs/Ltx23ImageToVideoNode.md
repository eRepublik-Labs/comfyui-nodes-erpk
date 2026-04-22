<!-- ABOUTME: Help documentation for the WaveSpeed LTX 2.3 Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a source image using Lightricks LTX 2.3 via WaveSpeed AI. -->

# WaveSpeed LTX 2.3 Image-to-Video

Animates a source image using Lightricks' LTX 2.3 model via the WaveSpeed AI API. Returns a URL to the generated video.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | String | "" | Source image URL to animate (required) |
| prompt | String | "" | Text description guiding the animation (required) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| resolution | Combo | 720p | Output resolution: 480p, 720p, or 1080p. Aspect ratio is inferred from the source image (optional) |
| duration | Int | 5 | Video duration in seconds, 5 to 20 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **Aspect ratio is inferred from the source image**, unlike the text-to-video variant which lets you pick 16:9 or 9:16.
- **Image URL input** — use `WaveSpeed Custom Upload Image` to upload a local image and get a URL.
- **Distinct generation from LTX 2 Pro** — LTX 2.3 supports longer durations (up to 20s) but does not emit synchronized audio.
- Both `image` and `prompt` are required and must be non-empty.
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
