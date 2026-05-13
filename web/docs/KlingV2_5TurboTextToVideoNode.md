<!-- ABOUTME: Help documentation for the Kling 2.5 Turbo Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates a short video from a text prompt using the Kling 2.5 Turbo Pro model. -->

# Kling 2.5 Turbo Text-to-Video

Generates a short video from a text prompt using the Kling 2.5 Turbo Pro model via the WaveSpeed AI API. WaveSpeed only exposes a Pro tier for this modality; the Combo is kept single-option so the UX matches the rest of the Kling node family.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Kling 2.5 Turbo Pro | Model variant (only Pro is offered for text-to-video) |
| prompt | String | "" | Text description of the desired scene and motion (max 2500 chars) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| negative_prompt | String | "" | Elements to suppress or avoid in the generated video (optional) |
| aspect_ratio | Combo | 16:9 | Aspect ratio of the output video: 16:9, 9:16, or 1:1 (optional) |
| guidance_scale | Float | 0.5 | Prompt adherence (0.0-1.0); higher values reduce creative deviation (optional) |
| duration | Combo | 5 | Video duration in seconds: 5 or 10 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **API endpoint:** `/api/v3/kwaivgi/kling-v2.5-turbo-pro/text-to-video`
- **Pro-only modality:** WaveSpeed does not expose a Std tier for Kling 2.5 Turbo text-to-video; the model Combo lists Pro only for parity with the rest of the Kling family
- **Required fields:** `prompt` must be non-empty
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
