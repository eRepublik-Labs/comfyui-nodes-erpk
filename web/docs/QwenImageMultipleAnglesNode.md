<!-- ABOUTME: Help documentation for the Qwen Image Multiple Angles ComfyUI node. -->
<!-- ABOUTME: Transforms images by adjusting viewing angle and distance parameters. -->

# Qwen Image Multiple Angles

Transforms reference images by adjusting viewing angle and distance. Supports horizontal rotation, vertical rotation, and distance adjustment with an optional guiding prompt.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| images | String | - | Reference images to transform, max 3 (comma-separated URLs) |
| prompt | String | "" | Text description to guide the transformation (optional) |
| client | WAVESPEED_AI_API_CLIENT | - | WaveSpeed API client (optional if API key is configured in Settings) |
| horizontal_angle | Int | 0 | Horizontal rotation angle, -90 to 90 degrees (optional) |
| vertical_angle | Int | 0 | Vertical rotation angle, -30 to 60 degrees (optional) |
| distance | Float | 1.0 | Subject distance factor, 0.0 to 2.0 (optional) |
| width | Int | 1024 | Image width, 256-1536, step 8 (optional) |
| height | Int | 1024 | Image height, 256-1536, step 8 (optional) |
| seed | Int | -1 | Random seed for reproducibility, -1 for random (optional) |
| output_format | Combo | jpeg | Output image format: jpeg, png, webp (optional) |
| enable_sync_mode | Boolean | false | Wait for completion before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64-encoded output instead of URL (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Transformed image |

## Notes

- **Pricing:** $0.02 per image
- **API Docs:** [Qwen Image Multiple Angles](https://wavespeed.ai/docs/docs-api/wavespeed-ai/qwen-image-edit-2509-multiple-angles)
- At least 1 reference image is required (up to 3)
- Angle and distance parameters are only sent when they differ from defaults
- Prompt is optional for this node
