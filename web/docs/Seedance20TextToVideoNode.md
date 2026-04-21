<!-- ABOUTME: Help documentation for the Seedance 2.0 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates short videos from text prompts using Bytedance Seedance 2.0. -->

# Bytedance Seedance 2.0 Text-to-Video

Generates a short video clip from a text prompt using Bytedance Seedance 2.0 via WaveSpeed AI.
Select between three model tiers to trade off quality and speed, then preview the returned URL
with the ERPK Preview Anything node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Seedance 2.0 | Model tier: Seedance 2.0 (standard), Seedance 2.0 Fast, or Seedance 2.0 Turbo |
| prompt | String | "" | Text description of the video to generate |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| duration | Int | 5 | Video duration in seconds (3-12) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9, 9:16, or 1:1 |
| resolution | Combo | 720p | Video resolution: 480p, 720p, or 1080p |
| seed | Int | -1 | Random seed for reproducibility; -1 for random |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video (plug into Preview Anything) |

## Notes

- **API Docs:** [Bytedance Seedance 2.0 Text-to-Video](https://wavespeed.ai/docs/docs-api/bytedance/seedance-2.0-text-to-video)
- Prompt is required and cannot be empty.
- Video jobs are long-running. The node polls every 10 seconds and times out after 15 minutes.
- Connect the `video_url` output to **Preview Anything** to play the result and download the file.
- Three endpoints are addressed by the model combo:
  - `Seedance 2.0` → `/api/v3/bytedance/seedance-2.0/text-to-video`
  - `Seedance 2.0 Fast` → `/api/v3/bytedance/seedance-2.0/text-to-video-fast`
  - `Seedance 2.0 Turbo` → `/api/v3/bytedance/seedance-2.0/text-to-video-turbo`
