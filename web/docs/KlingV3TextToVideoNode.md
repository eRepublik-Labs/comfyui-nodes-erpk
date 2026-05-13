<!-- ABOUTME: Help documentation for the Kling 3.0 Text-to-Video ComfyUI node. -->
<!-- ABOUTME: Generates a short video from a text prompt using Kling 3.0 Std, Pro, and 4K models. -->

# Kling 3.0 Text-to-Video

Generates a short video from a text prompt using Kling 3.0 models via the WaveSpeed AI API. Exposes the full documented parameter set: negative prompt, cfg_scale, sound, shot type, multi-prompt scene segmentation, and element list for visual consistency.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| model | Combo | Kling 3.0 | Model variant: Kling 3.0 (Std), Kling 3.0 Pro (higher quality), or Kling 3.0 4K (highest resolution) |
| prompt | String | "" | Text description of the video to generate (required unless `multi_prompt` is provided) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| duration | Int | 5 | Video duration in seconds, 3 to 15 (optional) |
| aspect_ratio | Combo | 16:9 | Aspect ratio of the output video: 16:9, 9:16, or 1:1 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| negative_prompt | String | "" | Elements to exclude from the generation (optional) |
| cfg_scale | Float | 0.5 | Prompt adherence strength, 0.0-1.0 (optional) |
| sound | Boolean | False | Enable synchronized audio generation (optional) |
| shot_type | Combo | intelligent | Shot composition mode: `intelligent` or `customize` (optional) |
| multi_prompt | String | "" | JSON array of scene-segmented prompts (mutually exclusive with `prompt`) (optional) |
| element_list | String | "" | JSON array of pre-generated element IDs for visual consistency — produce via the Kling Elements node (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | STRING | URL of the generated video — feed to `WaveSpeed Preview Video` to download/save |

## Notes

- **API endpoints:** `/api/v3/kwaivgi/kling-v3.0-std/text-to-video` (Std), `/api/v3/kwaivgi/kling-v3.0-pro/text-to-video` (Pro), and `/api/v3/kwaivgi/kling-v3.0-4k/text-to-video` (4K)
- **Prompt mutual exclusion:** either `prompt` or `multi_prompt` must be provided; supply `multi_prompt` as a JSON array of scene-segmented prompts for multi-shot generation
- **Element list:** populate `element_list` with IDs produced by the `Kling Elements` node to lock characters/styles across scenes
- **Namespace:** Kling 3.0 lives under `kling-v3.0-*`, distinct from Kling O3 (`kling-video-o3-*`)
- Video generation is long-running (polling interval 10s, 15-minute timeout)
- Connect the `video_url` output to the `WaveSpeed Preview Video` node to download and preview
