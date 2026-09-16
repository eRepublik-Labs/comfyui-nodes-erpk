<!-- ABOUTME: Help documentation for the MiniMax H3 Video Edit ComfyUI node. -->
<!-- ABOUTME: Rewrites lighting, style, environment or elements of an existing clip from a prompt. -->

# MiniMax H3 Video Edit

Rewrites lighting, style, environment or specific elements of an input video while the video itself drives identity, composition and motion. Chains directly off the `video_url` output of any video node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | What to change. Cite references as `<Picture N>` and `<Audio N>` |
| video_url | String | (empty) | Source video URL (optional in the schema, required to run) |
| reference_images | String | (empty) | Reference image URL(s), up to 9 (optional) |
| reference_audios | String | (empty) | Reference audio URL(s), up to 3 (optional) |
| reference_images_tensor | IMAGE | (none) | Reference images as an IMAGE batch, capped at 9. Takes precedence over reference_images (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| resolution | Combo | 480p | 480p, 540p, 768p or 1080p (optional) |
| aspect_ratio | Combo | auto | auto, 16:9, 9:16, 1:1, 4:3, 3:4, 21:9, 9:21. auto adapts to the input video (optional) |
| duration | Int | 0 | Output duration in seconds, 3-15. Below 3 follows the input clip (optional) |
| generate_audio | Boolean | true | Generate a new soundtrack. Off keeps the input's audio track (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the edited video, ready for Preview Anything |

## Cost

Billed per counted second, where counted seconds are input plus output duration, each capped at 15: about $0.05 at 480p, $0.075 at 540p, $0.125 at 768p and $0.25 at 1080p, plus about $0.02 per reference image or audio. A 10s clip edited at 480p counts 20 seconds, about $1.00.

## Notes

- Polling times out after 30 minutes on this node; edits run longer than generation
- There is no `-lora` twin for video edit, so the node has no loras socket
- Input clips longer than 15 seconds are capped at 15 for billing and processing
