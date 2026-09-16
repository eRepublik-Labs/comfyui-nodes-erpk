<!-- ABOUTME: Help documentation for the MiniMax H3 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates 4-15s video with native stereo audio from a text prompt via MiniMax's hosted H3. -->

# MiniMax H3 Text-to-Video

Generates a video clip with native stereo audio from a text prompt using MiniMax's hosted H3 endpoint.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Scene, action and camera movement, plus an Audio: line |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 4-15 (optional) |
| aspect_ratio | Combo | 16:9 | 16:9, 9:16, 1:1, 4:3, 3:4, 21:9 (optional) |
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

## Cost

Billed per generated second: $0.10/s at 768p and $0.14/s at 2k. A 15-second 2k clip is $2.10.

## Notes

- Output is MP4 with stereo audio
- Workflows saved with the earlier 480p/540p/1080p tiers or the 9:21 ratio are remapped on load (480p/540p to 768p, 1080p to 2k, 9:21 to 9:16)
