<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Lite Sequential ComfyUI node. -->
<!-- ABOUTME: Generates multiple coherent images at higher minimum resolution with cross-image consistency. -->

# Bytedance Seedream V5.0 Lite Sequential

Generates multiple coherent images with cross-image consistency at higher minimum resolution (1440px) using ByteDance's Seedream V5.0 Lite Sequential model.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Text description for image generation. The node automatically appends the image count |
| max_images | Int | 4 | Number of images to generate (1-15) |
| size_preset | Combo | "Custom" | Resolution preset. Select "Custom" to use manual width/height |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| width | Int | 2048 | Custom width in pixels, 1440-4096, step 8 (optional) |
| height | Int | 2048 | Custom height in pixels, 1440-4096, step 8 (optional) |
| show_aspect_ratio | Boolean | true | Show aspect ratio in node title (optional) |
| enable_sync_mode | Boolean | false | Wait for result before returning response (optional) |
| enable_base64_output | Boolean | false | Return BASE64 encoded output instead of URLs (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | IMAGE | Batch of generated images |

## Notes

- **Pricing:** $0.035/image
- **API Docs:** [Bytedance Seedream V5.0 Lite Sequential](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v5-0-lite-sequential)
- The node automatically appends "Generate a set of N consecutive." to your prompt
- All generated images maintain cross-image consistency
