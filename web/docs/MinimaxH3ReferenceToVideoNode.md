<!-- ABOUTME: Help documentation for the MiniMax H3 Reference-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates video guided by up to 9 reference images, 3 videos and 3 audios. -->

# MiniMax H3 Reference-to-Video

Generates video guided by reference images, videos and audio, with native stereo audio.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Prompt citing each reference by bracket tag. See below |
| reference_images | String | (empty) | Reference image URL(s), up to 9 (optional) |
| reference_videos | String | (empty) | Reference video URL(s), up to 3. Forces 480p output (optional) |
| reference_audios | String | (empty) | Reference audio URL(s), up to 3, each trimmed to 15s (optional) |
| reference_images_tensor | IMAGE | (none) | Reference images as a ComfyUI IMAGE batch, capped at 9. Takes precedence over reference_images (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Video duration in seconds. Range: 3-15 (optional) |
| aspect_ratio | Combo | 16:9 | 16:9, 9:16, 1:1, 4:3, 3:4, 21:9, 9:21 (optional) |
| resolution | Combo | 480p | 480p or 768p (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated video, ready for Preview Anything |

## You must cite references by tag

This is the part that catches people out. A reference is only used if the prompt names it with an exact bracket tag. Mentioning it in plain prose does nothing.

```
<Picture 1> walks through the doorway from <Picture 2>,
matching the camera move in <Video 1>.
Audio: <Audio 1>
```

Tags are numbered per type in input order: `<Picture 1>` to `<Picture 9>`, `<Video 1>` to `<Video 3>`, `<Audio 1>` to `<Audio 3>`.

A reference video's own audio automatically fills the earliest `<Audio>` slots before any standalone audio you supply, so number your audio tags with that in mind.

## At least one image or video is required

Audio alone is rejected. The node raises before spending anything if you supply neither an image nor a video.

## Cost

Every reference adds to the bill on top of the output:

| Item | Price |
|---|---|
| Output at 480p | $0.05 / second |
| Output at 768p | $0.125 / second |
| Each reference image | $0.02 |
| Each reference audio | $0.02 |
| Reference video | $0.05 / second |

WaveSpeed's worked example: a 10s 480p video with 2 reference images and a 5s reference video totals about $0.79, roughly four times the base rate.

## Notes

- Supplying any reference video forces 480p output
- Reference videos share a 15-second budget; longer inputs are trimmed
- Output is MP4 with stereo audio at 24fps
- Median generation time is around 279 seconds, longer than the other H3 nodes
