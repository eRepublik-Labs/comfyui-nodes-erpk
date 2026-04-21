<!-- ABOUTME: Help documentation for the WaveSpeed Veo 3.1 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates video from text prompts using Veo 3.1 billed through WaveSpeed. -->

# WaveSpeed Veo 3.1 Text-to-Video

Generates videos from text prompts using Google's Veo 3.1 model, billed through WaveSpeed's unified API. Veo 3.1 produces video with synchronized native audio.

This node is distinct from the `Veo Text to Video` node under `ERPK/Gemini/Veo`, which calls Google's direct API via the `google-genai` SDK. Use this WaveSpeed-billed variant if you prefer WaveSpeed's unified quota and billing.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description of the video to generate |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| duration | Int | 8 | Video duration in seconds, 4 to 8 (optional) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 (landscape) or 9:16 (portrait) (optional) |
| resolution | Combo | 1080p | Output resolution: 720p or 1080p (optional) |
| audio_enabled | Boolean | true | Generate synchronized native audio (optional) |
| negative_prompt | String | "" | Elements to exclude from the video (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | URL of the generated MP4 video. Pipe into `WaveSpeed Preview Video` to download/save. |

## Notes

- **API Docs:** [Veo 3.1 Text-to-Video](https://wavespeed.ai/docs/docs-api/google/google-veo3.1-text-to-video)
- **Endpoint:** `/api/v3/google/veo3.1/text-to-video`
- Distinct from `VeoTextToVideo` (Gemini direct API). Node class: `WaveSpeedVeo31TextToVideoNode`.
- Video generation is asynchronous; the node polls every 10s with a 15-minute total timeout.
- Prompt is required.
- Veo 3.1 natively generates synchronized audio; disable with `audio_enabled=false` if you need a silent track.
