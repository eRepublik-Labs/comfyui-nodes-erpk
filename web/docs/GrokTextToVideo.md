<!-- ABOUTME: Help documentation for the Grok Text to Video ComfyUI node. -->
<!-- ABOUTME: Text-to-video generation via xAI's grok-imagine-video model. -->

# Grok Text to Video

Generates a short video clip from a text prompt using xAI's Grok video model. The xAI SDK polls internally — this node blocks until the video is ready and returns its URL.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| prompt | String | (empty) | Description of the video to generate |
| model | Combo | grok-imagine-video | Video model (optional) |
| aspect_ratio | Combo | 16:9 | One of: 16:9, 9:16, 1:1, 4:3, 3:4, 3:2, 2:3 (optional) |
| resolution | Combo | 720p | 480p (faster) or 720p (HD) (optional) |
| duration | Int | 5 | Video length in seconds (1–15) (optional) |
| seed | Int | -1 | Cache-invalidation only — not forwarded to xAI. -1 randomizes (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video |

## Notes

- Generation takes 30 s – several minutes depending on duration/resolution.
- The xAI SDK abstracts polling internally; no manual `wait_for_task` needed.
- Async-enabled — multiple Grok Text to Video nodes in the same workflow run their polling loops concurrently (see the v2026.5.13 release for the async parallelism mechanism).
- Use a Preview Video node downstream to view + save the result, or chain into Grok Video Edit / Extend.
