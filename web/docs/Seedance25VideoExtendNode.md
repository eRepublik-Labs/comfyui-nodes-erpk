<!-- ABOUTME: Help documentation for the Bytedance Seedance 2.5 Video Extend ComfyUI node. -->
<!-- ABOUTME: Continues an existing video clip past its final frame via WaveSpeed AI. -->

# Bytedance Seedance 2.5 Video Extend

Continues an existing video clip past its final frame using Bytedance Seedance 2.5, reading up to the last 30 seconds of the source as context. The source clip is taken as a URL, so this node chains directly off the video_url output of any video node in this package.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | How the video should continue: action, camera, lighting, mood |
| video_url | String | (empty) | Source video URL. Connect the video_url output of any video node (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Length of the new segment in seconds. Range: 4-30 (optional) |
| resolution | Combo | 720p | 480p, 720p, 1080p, 4k (optional) |
| generate_audio | Boolean | true | Generate audio for the new segment, preserving the original audio (optional) |
| seed | Int | -1 | Cache control only, never sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the extended video, ready for Preview Anything |

## The seed does not reach the API

Seedance 2.5 accepts no seed on any endpoint. A fixed seed reuses the video you already paid for; -1 regenerates on every queue.

## Cost

Billed on the context read from the source plus the new segment, so a long source clip raises the price even when the new segment is short. Roughly $0.11/s at 480p, $0.22/s at 720p, $0.55/s at 1080p and $1.10/s at 4k, with the context length clamped to between 2 and 30 seconds.

## Notes

- A source video URL is required
- The duration setting controls the new segment only, not the finished video
- Median generation time runs to several minutes; the node polls for up to 30 minutes
