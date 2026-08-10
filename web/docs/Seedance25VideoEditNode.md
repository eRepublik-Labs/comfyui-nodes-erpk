<!-- ABOUTME: Help documentation for the Bytedance Seedance 2.5 Video Edit ComfyUI node. -->
<!-- ABOUTME: Rewrites an existing video clip from a text prompt via WaveSpeed AI. -->

# Bytedance Seedance 2.5 Video Edit

Rewrites an existing video clip from a text prompt using Bytedance Seedance 2.5. The source clip is taken as a URL, so this node chains directly off the video_url output of any video node in this package.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | What to change in the video. The service prepends "Edit the input video." to it |
| video_url | String | (empty) | Source video URL. Connect the video_url output of any video node (optional) |
| model | Combo | Seedance 2.5 | Model tier: Seedance 2.5, Seedance 2.5 Turbo (faster) |
| reference_images | String | (empty) | Reference image URL(s) guiding style, identity or appearance. Up to 4 (optional) |
| reference_audios | String | (empty) | Reference audio URL(s) guiding soundtrack or voice. Up to 4 (optional) |
| reference_images_tensor | IMAGE | (none) | Reference images as a ComfyUI IMAGE batch. Takes precedence over reference_images (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| resolution | Combo | 720p | 480p, 720p, 1080p, 4k (optional) |
| generate_audio | Boolean | true | Generate audio synchronized with the edited video (optional) |
| seed | Int | -1 | Cache control only, never sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the edited video, ready for Preview Anything |

## There is no duration control

Output duration and aspect ratio follow the input clip. Clips longer than 30 seconds are trimmed to 30; clips shorter than 4 seconds are padded to 4.

## The seed does not reach the API

Seedance 2.5 accepts no seed on any endpoint. A fixed seed reuses the video you already paid for; -1 regenerates on every queue.

## Cost

Billed on the combined input and output duration: roughly $0.11/s at 480p, $0.22/s at 720p, $0.55/s at 1080p and $1.10/s at 4k. A 12-second clip at 720p costs about $5.28, since both the input and the output count.

## Notes

- A source video URL is required
- Median generation time runs to several minutes; the node polls for up to 30 minutes
