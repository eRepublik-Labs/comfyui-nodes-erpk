<!-- ABOUTME: Help documentation for the Grok Video Edit ComfyUI node. -->
<!-- ABOUTME: Edits an existing video URL via text prompt. -->

# Grok Video Edit

Edits an existing video using a text prompt. The output inherits the source video's duration (capped at 8.7 s), aspect ratio, and resolution (capped at 720p), per xAI's documentation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| prompt | String | (empty) | Editing instructions describing the desired changes |
| video_url | String | (empty) | Source video to edit: a public URL or a base64 data URI |
| model | Combo | grok-imagine-video | Video model. Only option: grok-imagine-video; grok-imagine-video-1.5 takes no video input (optional) |
| seed | Int | -1 | Cache-invalidation only — not forwarded to xAI. -1 randomizes (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the edited video |

## Notes

- The source is a public URL or a base64 data URI. xAI also accepts a Files API `file_id`, which this node does not expose.
- Output capped at 720p even if the source was higher resolution (xAI limitation).
- Chain Edit nodes by feeding each `video_url` output into the next Edit's `video_url` input.
- Async-enabled — runs concurrently with other Grok video nodes.
