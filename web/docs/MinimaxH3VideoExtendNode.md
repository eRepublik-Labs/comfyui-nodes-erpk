<!-- ABOUTME: Help documentation for the MiniMax H3 Video Extend ComfyUI node. -->
<!-- ABOUTME: Appends a new segment after a clip's last frame, optionally toward a target end frame. -->

# MiniMax H3 Video Extend

Generates a new segment from the input video's last frame and appends it to the original. Chains directly off the `video_url` output of any video node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | How the video continues, plus an Audio: line |
| video_url | String | (empty) | Source video URL. Required unless the video input is connected (optional) |
| last_frame | IMAGE | (none) | Target end frame for the new segment. Takes precedence over last_frame_url (optional) |
| last_frame_url | String | (empty) | Target end frame image URL (optional) |
| client | WAVESPEED_AI_API_CLIENT | (none) | WaveSpeed API client (optional if API key is in Settings) |
| duration | Int | 5 | Length of the new segment in seconds, 3-15 (optional) |
| resolution | Combo | 480p | Resolution of the new segment: 480p, 540p, 768p or 1080p (optional) |
| seed | Int | -1 | Generation seed, sent to the API (optional) |
| video | VIDEO | (none) | Source clip as a ComfyUI VIDEO, uploaded to WaveSpeed. Takes precedence over video_url (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the extended video, ready for Preview Anything |

## Duration is the new segment

The duration widget sets how many seconds are appended, not the total output length. The original clip is returned with the new segment attached.

## Cost

Billed per second of the new segment: about $0.04/s at 480p, $0.06/s at 540p, $0.08/s at 768p and $0.16/s at 1080p.

## Two ways to supply the source clip

Connect the video_url output of another node to chain, or connect a ComfyUI VIDEO to the video input and the node uploads it to WaveSpeed first. The typed input wins when both are set.

## Notes

- With a target last frame, the new segment interpolates from the source's last frame to that image
- There is no `-lora` twin for video extend, so the node has no loras socket
