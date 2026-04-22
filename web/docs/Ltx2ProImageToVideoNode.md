<!-- ABOUTME: Help documentation for the Lightricks LTX 2 Pro Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a source image into short-form video with optional synchronized audio. -->

# Lightricks LTX 2 Pro Image-to-Video

Animates a source image into short-form video using Lightricks' LTX 2 Pro model via the WaveSpeed AI API. Supports synchronized audio generation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | String | "" | Source image URL to animate (required) |
| prompt | String | "" | Text description guiding the animation (max 5000 chars, required) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| duration | Combo | 6 | Output duration in seconds: 6, 8, or 10 (optional) |
| generate_audio | Boolean | true | Generate synchronized audio with the video (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **Synchronized audio** — LTX 2 Pro is the only LTX variant on WaveSpeed that emits audio alongside the video. Toggle `generate_audio=false` for video-only output.
- **Image URL input** — use `WaveSpeed Custom Upload Image` to upload a local image and get a URL.
- **Fixed duration set** — only 6, 8, or 10 seconds. For longer clips, use the LTX 2.3 Image-to-Video node.
- **Distinct generation from LTX 2.3** — LTX 2 Pro focuses on short-form creative output with audio; LTX 2.3 focuses on longer silent clips with configurable resolution.
- Both `image` and `prompt` are required and must be non-empty.
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
