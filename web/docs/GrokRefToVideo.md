<!-- ABOUTME: Help documentation for the Grok Reference to Video ComfyUI node. -->
<!-- ABOUTME: Generates a video guided by up to 3 reference images. -->

# Grok Reference to Video

Generates a video guided by one to three reference images and a text prompt. References influence the appearance of subjects in the output without locking in the first frame.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| prompt | String | (empty) | Video description. May reference inputs via `<IMAGE_1>`, `<IMAGE_2>`, `<IMAGE_3>` tokens |
| reference_images | IMAGE | — | Batched IMAGE tensor — up to 3 frames used as references |
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

- Reference images are converted to base64 PNG data URIs automatically.
- Distinct from image-to-video: references *influence* the video without becoming the opening frame.
- Use cases: virtual try-on, product placement, character-consistent storytelling. Address specific references inline via `<IMAGE_N>` tokens in the prompt.
- Async-enabled — runs concurrently with other Grok video nodes.
