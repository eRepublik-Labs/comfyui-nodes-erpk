<!-- ABOUTME: Help documentation for the MiniMax H3 Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a first frame, optionally interpolating toward a last frame. -->

# MiniMax H3 Image-to-Video

Animates a first-frame image with native stereo audio. Supply a last frame and the model interpolates between the two.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Motion and camera movement, plus an Audio: line |
| first_frame | IMAGE | (none) | First frame as a ComfyUI IMAGE tensor. Preferred over first_frame_url (optional) |
| first_frame_url | String | (empty) | First frame image URL. Fallback when first_frame is not connected (optional) |
| last_frame | IMAGE | (none) | Last frame as a ComfyUI IMAGE tensor. The model interpolates between frames (optional) |
| last_frame_url | String | (empty) | Last frame image URL. Fallback when last_frame is not connected (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 3-15 (optional) |
| resolution | Combo | 480p | 480p or 768p (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video, ready for Preview Anything |

## No aspect ratio control

The output canvas follows the first frame's aspect ratio, so there is nothing to set.

## There is no audio toggle

Audio is generated natively in one pass and steered by an `Audio:` line in the prompt.

## Cost

About $0.04/s at 480p and $0.10/s at 768p.

## Notes

- A first frame is required, as either an IMAGE tensor or a URL
- Output is MP4 with stereo audio at 24fps
- Duration snaps to the model's frame grid, so a 5s request lands near 5.2s
- Median generation time is around 141 seconds
