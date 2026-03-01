<!-- ABOUTME: Help documentation for the Bytedance Seedream V4 Sequential ComfyUI node. -->
<!-- ABOUTME: Generates multiple coherent images with cross-image consistency from a text prompt. -->

# Bytedance Seedream V4 Sequential

Generates multiple coherent images with cross-image consistency in a single pipeline using ByteDance's Seedream V4 Sequential model.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description for image generation. The node automatically appends the image count |
| max_images | Int | 4 | Number of images to generate (1-15) |
| size_preset | Combo | "Custom" | Resolution preset. Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 1408 | Custom width in pixels, 320-4096, step 8 (optional) |
| height | Int | 1408 | Custom height in pixels, 320-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |
| enable_sync_mode | Boolean | false | Wait for result before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64 encoded output instead of URLs (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | IMAGE | Batch of generated images |

## Notes

- **Pricing:** $0.027/image
- **API Docs:** [Bytedance Seedream V4 Sequential](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v4-sequential)
- The node automatically appends "Generate a set of N consecutive." to your prompt for API compliance
- All generated images maintain cross-image consistency
