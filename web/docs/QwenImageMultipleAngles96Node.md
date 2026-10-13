<!-- ABOUTME: Help documentation for the Qwen Image Multiple Angles (96 poses) ComfyUI node. -->
<!-- ABOUTME: Re-renders a subject from one of 96 camera poses on WaveSpeed's edit-multiple-angles model. -->

# Qwen Image Multiple Angles (96 poses)

Re-renders the subject of 1 to 3 reference images from a new camera pose. The model renders 96 poses: 8 positions around the subject, 4 camera heights and 3 framing distances. The dropdowns offer exactly those poses.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| reference_images | IMAGE | - | Reference images as an IMAGE batch, max 3, one image per slice. Takes precedence over `reference_images_url`; sent inline as base64, no upload (optional) |
| reference_images_url | String | "" | Reference image URLs, max 3, separated by commas or newlines. Ignored when `reference_images` is connected (optional) |
| prompt | String | "" | Optional guidance appended to the camera-angle prompt (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| azimuth | Combo | front (0°) | front (0°), front-right (45°), right side (90°), back-right (135°), back (180°), back-left (225°), left side (270°), front-left (315°) (optional) |
| elevation | Combo | eye level (0°) | low angle (-30°), eye level (0°), elevated (30°), high angle (60°) (optional) |
| framing | Combo | medium | close-up, medium, wide (optional) |
| seed | Int | -1 | Generation seed, sent to the API. A fixed seed reproduces the result and lets ComfyUI reuse the cached output; -1 for random (optional) |
| output_format | Combo | jpeg | Output image format: jpeg, png, webp (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Image from the chosen camera pose |

## Notes

- **API Docs:** [Qwen Image Edit Multiple Angles](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit-multiple-angles)
- $0.025 per image
- At least one image (`reference_images` or `reference_images_url`) is required
- The older **Qwen Image Multiple Angles** node calls a different model (edit-2509) with continuous angles (horizontal -90 to 90, distance 0 to 2)
