<!-- ABOUTME: Help documentation for the MiniMax H3 Image-to-Video ComfyUI node. -->
<!-- ABOUTME: Animates a first frame toward an optional last frame via MiniMax's hosted H3. -->

# MiniMax H3 Image-to-Video

Animates a first-frame image with native stereo audio using MiniMax's hosted H3 endpoint. Supply a last frame and the model interpolates between the two.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Motion and camera movement, plus an Audio: line |
| first_frame | IMAGE | (none) | First frame as a ComfyUI IMAGE tensor. Preferred over first_frame_url (optional) |
| first_frame_url | String | (empty) | First frame image URL. Fallback when first_frame is not connected (optional) |
| last_frame | IMAGE | (none) | Last frame as a ComfyUI IMAGE tensor. The model interpolates between frames (optional) |
| last_frame_url | String | (empty) | Last frame image URL. Fallback when last_frame is not connected (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 4-15 (optional) |
| resolution | Combo | 768p | 768p or 2k (optional) |
| seed | Int | -1 | Cache control only; never sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video, ready for Preview Anything |

## Which edition this calls

This node calls MiniMax's own hosted H3 endpoint on WaveSpeed (`minimax/h3/...`), not the open-weights edition WaveSpeed hosts itself (`wavespeed-ai/minimax-h3/...`). The hosted edition offers 768p and 2k, 4-15s clips, and takes no seed or LoRA parameters. The MiniMax H3 Text-to-Image, Image Edit, Video Edit, Video Extend and LoRA Stack nodes still use the open-weights edition.

## The seed is cache control only

The endpoint documents no seed, so the widget is never sent. A fixed seed lets ComfyUI reuse the video you already paid for; -1 generates again on every queue.

## There is no audio toggle

Audio is generated natively in one pass and steered by an `Audio:` line in the prompt, for example:

```
A lighthouse in a storm, slow dolly in.
Audio: waves crashing, wind, a distant foghorn.
```

## No aspect ratio control

The output canvas follows the first frame's aspect ratio, so there is nothing to set. Frames may be 256-5760 pixels per side.

## Cost

$0.10/s at 768p and $0.14/s at 2k.

## Notes

- A first frame is required, as either an IMAGE tensor or a URL
- Output is MP4 with stereo audio
- Workflows saved with the earlier 480p/540p/1080p tiers are remapped on load (480p/540p to 768p, 1080p to 2k)
