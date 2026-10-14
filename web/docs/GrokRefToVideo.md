<!-- ABOUTME: Help documentation for the Grok Reference to Video ComfyUI node. -->
<!-- ABOUTME: Generates a video guided by up to 7 (grok-imagine-video) or 14 (grok-imagine-video-1.5) reference images. -->

# Grok Reference to Video

Generates a video guided by reference images and a text prompt: up to 7 images on grok-imagine-video, up to 14 on grok-imagine-video-1.5. References influence the appearance of subjects in the output without locking in the first frame.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| prompt | String | (empty) | Video description. May reference inputs via `<IMAGE_0>`, `<IMAGE_1>`, ... tokens (the first image is `<IMAGE_0>`) |
| reference_images | IMAGE | — | Batched IMAGE tensor used as references: up to 7 frames on grok-imagine-video, 14 on grok-imagine-video-1.5. A larger batch is rejected before the API call |
| model | Combo | grok-imagine-video | Video model: grok-imagine-video, grok-imagine-video-1.5. grok-imagine-video-1.5-lite takes no reference images, so it is not offered (optional) |
| aspect_ratio | Combo | 16:9 | One of: 16:9, 9:16, 1:1, 4:3, 3:4, 3:2, 2:3 (optional) |
| resolution | Combo | 720p | 480p (faster) or 720p (HD). Reference-to-video tops out at 720p on every model (optional) |
| duration | Int | 5 | Video length in seconds: 1–15 on grok-imagine-video-1.5, 1–10 on grok-imagine-video (longer is rejected before the API call) (optional) |
| seed | Int | -1 | Cache-invalidation only — not forwarded to xAI. -1 randomizes (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video |

## Notes

- Reference images are converted to base64 JPEG data URIs automatically.
- Distinct from image-to-video: references *influence* the video without becoming the opening frame.
- Use cases: virtual try-on, product placement, character-consistent storytelling. Address specific references inline via `<IMAGE_N>` tokens in the prompt, counting from `<IMAGE_0>`.
- Async-enabled — runs concurrently with other Grok video nodes.
