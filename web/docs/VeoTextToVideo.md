<!-- ABOUTME: Help documentation for the Veo Text to Video ComfyUI node. -->
<!-- ABOUTME: Generates videos from text prompts using Google's Veo models. -->

# Veo Text to Video

Generates videos from text prompts using Google's Veo models. Veo 3.1 models generate video with synchronized audio.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GEMINI_API_CLIENT | - | Gemini API client from Gemini API Config node |
| prompt | String | "" | Text description of the video to generate (max 2500 characters) |
| reference_images | IMAGE | - | Up to 3 reference images (batched IMAGE) for style/content guidance. Veo 3.1 and 3.1 Fast only; ignored on Lite. Requires duration 8s and aspect ratio 16:9; other values are rejected before the call (optional) |
| model | Combo | veo-3.1-generate-preview | Veo model: veo-3.1-generate-preview, veo-3.1-fast-generate-preview, veo-3.1-lite-generate-preview (optional) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 (landscape) or 9:16 (portrait) (optional) |
| resolution | Combo | 720p | Output resolution: 720p, 1080p, 4k. Lite has no 4k (clamped to 1080p). 1080p and 4k only support 8s, so a shorter duration is raised to 8s (optional) |
| duration_seconds | Combo | 8 | Video duration: 4, 6 or 8 seconds. The 5 option is kept only so older workflows still load; it is sent as the nearest valid value (optional) |
| person_generation | Combo | allow_adult | Person generation safety. Text-to-video accepts allow_all, or allow_adult in EU/UK/CH/MENA where that is the only allowed value; dont_allow is rejected before the API call (optional) |
| seed | Int | -1 | Cache control only, never sent to the API (the Gemini Developer API takes no Veo seed). A fixed seed reuses the video already generated; -1 generates again on every queue. Range: -1 to 4294967295 (optional) |
| output_directory | String | "" | Directory to save video. Empty uses ComfyUI output folder (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_path | String | File path to the generated .mp4 video |

## Notes

- Video generation is asynchronous and may take 2-10 minutes depending on duration and model
- Veo 3.1 models generate synchronized audio along with video
- The node polls every 20 seconds and times out after 40 minutes
- Pricing per second of output, with audio: Veo 3.1 $0.40 (720p, 1080p) / $0.60 (4k); Veo 3.1 Fast $0.10 (720p) / $0.12 (1080p) / $0.30 (4k); Veo 3.1 Lite $0.05 (720p) / $0.08 (1080p)
- Google shuts down all three Veo 3.1 preview models on 2026-10-22; the listed replacement is Gemini Omni Flash (see the Gemini Omni Video node)
