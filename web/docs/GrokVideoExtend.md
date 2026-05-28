<!-- ABOUTME: Help documentation for the Grok Video Extend ComfyUI node. -->
<!-- ABOUTME: Appends new content to an existing video by URL. -->

# Grok Video Extend

Appends new content to the end of an existing video. The `duration` parameter controls the **length of the extension only**, not the total output length.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| video_url | String | (empty) | Public HTTPS URL of the source video to extend |
| duration | Int | 5 | Length of the **extended portion only**, in seconds (1–15). A 10 s source + duration=5 = 15 s output |
| prompt | String | (empty) | Optional guidance for the new content (optional) |
| model | Combo | grok-imagine-video | Video model (optional) |
| seed | Int | -1 | Cache-invalidation only — not forwarded to xAI. -1 randomizes (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the extended video |

## Notes

- The xAI extension endpoint takes ~5 s polling intervals internally; total wait scales with the requested extension length.
- Chain extensions to build longer videos: feed the output `video_url` into the next Extend's `video_url` input.
- Source video must be a publicly accessible HTTPS URL.
- Async-enabled — runs concurrently with other Grok video nodes.
