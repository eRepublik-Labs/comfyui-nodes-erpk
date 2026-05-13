<!-- ABOUTME: Help documentation for the Veo Image to Video ComfyUI node. -->
<!-- ABOUTME: Generates videos from an input image and optional text prompt using Veo models. -->

# Veo Image to Video

Generates videos from an input image and optional text prompt using Google's Veo models. The image serves as the first frame or style reference.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GEMINI_API_CLIENT | - | Gemini API client from Gemini API Config node |
| image | IMAGE | - | Input image to generate video from (used as first frame) |
| prompt | String | "" | Text description to guide the video generation (optional) |
| model | Combo | veo-3.1-generate-preview | Veo model: veo-3.1-generate-preview, veo-3.1-fast-generate-preview, veo-3.0-generate-001, veo-3.0-fast-generate-001, veo-2.0-generate-001 (optional) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 (landscape) or 9:16 (portrait) (optional) |
| duration_seconds | Combo | 8 | Video duration: 5, 6, 7, or 8 seconds (optional) |
| person_generation | Combo | allow_adult | Person generation safety: allow_adult, dont_allow, allow_all. Veo 3 only supports allow_all (optional) |
| enhance_prompt | Boolean | true | Let the model enhance your prompt for better results (optional) |
| negative_prompt | String | "" | Elements to exclude from the video (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random. Range: -1 to 4294967295 (optional) |
| output_directory | String | "" | Directory to save video. Empty uses ComfyUI output folder (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_path | String | File path to the generated .mp4 video |

## Notes

- The input image is used as the first frame or style reference for the generated video
- Prompt is optional for image-to-video; the model will animate the image based on its content
- Veo 3+ models generate synchronized audio along with video
- Video generation is asynchronous and may take 2-10 minutes
- Pricing: $0.75 per second of video output for Veo 3+ models

## Gotchas / undocumented constraints

These rules aren't in Google's published Veo parameter table but are confirmed by Google staff and senior developers in the discussion thread at https://discuss.ai.google.dev/t/veo-3-1-reference-images-docs-say-available-api-says-not-supported/111853. The node pre-validates them and raises a clear error before the API call, so you don't wait several minutes for the opaque `400 "Your use case is currently not supported"` response.

- **Using `last_frame_image` (image + last-frame interpolation) requires `duration_seconds = 8`.** 4-second and 6-second durations fail with the opaque 400 after several minutes of wasted generation time.
- **Using `reference_images` requires `duration_seconds = 8` AND `aspect_ratio = "16:9"`.** Portrait `9:16` is not supported with reference images.
- **`reference_images` and `last_frame_image` are mutually exclusive.** Use one or the other, never both — the API rejects requests that mix them.
