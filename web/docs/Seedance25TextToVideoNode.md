<!-- ABOUTME: Help documentation for the Bytedance Seedance 2.5 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates 4-30s video up to 4k from a text prompt via WaveSpeed AI. -->

# Bytedance Seedance 2.5 Text-to-Video

Generates a video clip from a text prompt using Bytedance Seedance 2.5. Supports durations from 4 to 30 seconds and resolutions up to 4k, with optional reference images, videos and audio for style, motion and soundtrack guidance.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Seedance 2.5 | Model tier: Seedance 2.5, Seedance 2.5 Turbo (faster) |
| prompt | String (multiline) | (empty) | Text description of the video to generate |
| reference_images | String | (empty) | Reference image URL(s) for style/character/composition. Up to 4 (optional) |
| reference_videos | String | (empty) | Reference video URL(s) for motion and pacing. Up to 4, total up to 30s (optional) |
| reference_audios | String | (empty) | Reference audio URL(s) for soundtrack guidance. Up to 4, total up to 30s (optional) |
| reference_images_tensor | IMAGE | (none) | Reference images as a ComfyUI IMAGE batch. Takes precedence over reference_images (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 4-30 (optional) |
| aspect_ratio | Combo | 16:9 | 16:9, 9:16, 4:3, 3:4, 1:1, 21:9 (optional) |
| resolution | Combo | 720p | 480p, 720p, 1080p, 4k (optional) |
| generate_audio | Boolean | true | Generate native audio synchronized with the video (optional) |
| seed | Int | -1 | Cache control only, never sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video, ready for Preview Anything |

## The seed does not reach the API

Seedance 2.5 accepts no seed on any endpoint, so this widget exists purely to control ComfyUI's cache. A fixed seed lets the graph reuse the video you already paid for; -1 regenerates on every queue. Changing it does not change what the model produces.

## Cost

Priced per second of output and rising steeply with resolution: roughly $0.18/s at 480p, $0.36/s at 720p, $0.90/s at 1080p and $1.80/s at 4k. A 30-second 4k clip is therefore a large charge. Runs that supply reference videos are billed on the combined reference and output duration, at a lower per-second rate.

## Notes

- Negative prompts are not supported; state exclusions inline in the prompt
- Median generation time is around 3-4 minutes; the node polls for up to 30 minutes
- Cancel is honoured mid-poll
