<!-- ABOUTME: Help documentation for the Bytedance Seedance 2.5 Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a start image, optionally steering toward an ending frame. -->

# Bytedance Seedance 2.5 Image-to-Video

Animates a start image using Bytedance Seedance 2.5. Supply an ending frame to steer where the clip finishes. Output aspect ratio follows the input image, so there is no aspect ratio control.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Text description of the motion to generate |
| start_frame | IMAGE | (none) | Start frame as a ComfyUI IMAGE tensor. Preferred over start_frame_url (optional) |
| start_frame_url | String | (empty) | Start frame image URL. Fallback when start_frame is not connected (optional) |
| last_frame | IMAGE | (none) | Ending frame as a ComfyUI IMAGE tensor. Steers the clip toward this image (optional) |
| last_frame_url | String | (empty) | Ending frame image URL. Fallback when last_frame is not connected (optional) |
| model | Combo | Seedance 2.5 | Model tier: Seedance 2.5, Seedance 2.5 Turbo (faster), Seedance 2.5 Spicy |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 4-30 (optional) |
| resolution | Combo | 720p | 480p, 720p, 1080p, 4k (optional) |
| generate_audio | Boolean | true | Generate native audio synchronized with the video (optional) |
| seed | Int | -1 | Cache control only, never sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video, ready for Preview Anything |

## The seed does not reach the API

Seedance 2.5 accepts no seed on any endpoint. A fixed seed reuses the video you already paid for; -1 regenerates on every queue.

## Cost

Roughly $0.18/s at 480p, $0.36/s at 720p, $0.90/s at 1080p and $1.80/s at 4k.

## Notes

- A start frame is required, as either an IMAGE tensor or a URL
- Output aspect ratio follows the input image and cannot be set
- Median generation time is around 3-4 minutes; the node polls for up to 30 minutes
