<!-- ABOUTME: Help documentation for the MiniMax H3 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates 3-15s video with native stereo audio from a text prompt. -->

# MiniMax H3 Text-to-Video

Generates a video clip with native stereo audio from a text prompt, at 24fps in a single pass.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Scene, action and camera movement, plus an Audio: line |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 3-15 (optional) |
| aspect_ratio | Combo | 16:9 | 16:9, 9:16, 1:1, 4:3, 3:4, 21:9, 9:21 (optional) |
| resolution | Combo | 480p | 480p, 540p, 768p or 1080p (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |
| loras | MINIMAX_H3_LORAS | (none) | LoRA stack from the MiniMax H3 LoRA Stack node. When connected the call goes to the -lora twin (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video, ready for Preview Anything |

## There is no audio toggle

Audio is generated natively alongside the picture in one pass. You steer it by writing an `Audio:` line into the prompt, for example:

```
A lighthouse in a storm, slow dolly in.
Audio: waves crashing, wind, a distant foghorn.
```

Omitting the line still produces audio; it just will not be directed.

## The seed is real

Unlike the Seedance 2.5 nodes, MiniMax H3 accepts a seed and honours it. A fixed seed reproduces the same video and lets ComfyUI reuse the cached result. -1 generates a new one on every queue.

## Cost

Billed per generated second: about $0.04/s at 480p, $0.06/s at 540p, $0.08/s at 768p and $0.16/s at 1080p. With a LoRA stack connected the -lora twin charges about $0.05 / $0.075 / $0.10 / $0.20 per second. A 15-second 768p clip is around $1.20.

## Notes

- Output is MP4 with stereo audio at 24fps
- Duration snaps to the model's frame grid, so a 5s request lands near 5.2s
- 768p is the model's native canvas; 1080p is upscaled full HD
- Median generation time is around 138 seconds
