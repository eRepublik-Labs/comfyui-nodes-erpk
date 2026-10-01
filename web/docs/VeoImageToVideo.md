<!-- ABOUTME: Help documentation for the Veo Image to Video ComfyUI node. -->
<!-- ABOUTME: Generates videos from an input image and optional text prompt using Veo models. -->

# Veo Image to Video

Generates videos from an input image and optional text prompt using Google's Veo models. The image is the first frame of the video.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GEMINI_API_CLIENT | - | Gemini API client from Gemini API Config node |
| image | IMAGE | - | Input image to generate video from (used as first frame) |
| last_frame_image | IMAGE | - | Last frame for first-to-last interpolation, on every Veo 3.1 model including Lite. Requires duration_seconds = 8 (optional) |
| reference_images | IMAGE | - | Up to 3 reference images (batched IMAGE). Veo 3.1 and 3.1 Fast only. Requires duration_seconds = 8 and aspect_ratio = 16:9; cannot be combined with last_frame_image (optional) |
| prompt | String | "" | Text description to guide the video generation (optional) |
| model | Combo | veo-3.1-generate-preview | Veo model: veo-3.1-generate-preview, veo-3.1-fast-generate-preview, veo-3.1-lite-generate-preview (optional) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 (landscape) or 9:16 (portrait) (optional) |
| resolution | Combo | 720p | Output resolution: 720p, 1080p, 4k. Lite has no 4k (clamped to 1080p). 1080p and 4k only support 8s, so a shorter duration is raised to 8s (optional) |
| duration_seconds | Combo | 8 | Video duration: 4, 6 or 8 seconds. The 5 option is kept only so older workflows still load; it is sent as the nearest valid value (optional) |
| person_generation | Combo | allow_adult | Person generation safety. Image-to-video accepts allow_adult only; allow_all and dont_allow are rejected before the API call (optional) |
| seed | Int | -1 | Cache control only, never sent to the API (the Gemini Developer API takes no Veo seed). A fixed seed reuses the video already generated; -1 generates again on every queue. Range: -1 to 4294967295 (optional) |
| output_directory | String | "" | Directory to save video. Empty uses ComfyUI output folder (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_path | String | File path to the generated .mp4 video |

## Notes

- The input image is used as the first frame of the generated video
- Prompt is optional for image-to-video; the model will animate the image based on its content
- Veo 3.1 models generate synchronized audio along with video
- Video generation is asynchronous and may take 2-10 minutes
- Pricing per second of output, with audio: Veo 3.1 $0.40 (720p, 1080p) / $0.60 (4k); Veo 3.1 Fast $0.10 (720p) / $0.12 (1080p) / $0.30 (4k); Veo 3.1 Lite $0.05 (720p) / $0.08 (1080p)
- Google shuts down all three Veo 3.1 preview models on 2026-10-22; the listed replacement is Gemini Omni Flash (see the Gemini Omni Video node)

## Gotchas / undocumented constraints

Google's Veo parameter table documents only the 8s rule for reference images; the other rules below are confirmed by Google staff and senior developers in the discussion thread at https://discuss.ai.google.dev/t/veo-3-1-reference-images-docs-say-available-api-says-not-supported/111853. The node pre-validates them and raises a clear error before the API call, so you don't wait several minutes for the opaque `400 "Your use case is currently not supported"` response.

- **Using `last_frame_image` (image + last-frame interpolation) requires `duration_seconds = 8`.** 4-second and 6-second durations fail with the opaque 400 after several minutes of wasted generation time.
- **Using `reference_images` requires `duration_seconds = 8` AND `aspect_ratio = "16:9"`.** Portrait `9:16` is not supported with reference images.
- **`reference_images` and `last_frame_image` are mutually exclusive.** Use one or the other, never both — the API rejects requests that mix them.
