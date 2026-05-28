<!-- ABOUTME: Help documentation for the Grok Image Generation ComfyUI node. -->
<!-- ABOUTME: Text-to-image via xAI's grok-imagine-image-quality model. -->

# Grok Image Generation

Generates one or more images from a text prompt using xAI's Grok image model. Returns a batched IMAGE tensor ready for downstream ComfyUI workflows.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Description of the image to generate |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-imagine-image-quality | Image model (optional) |
| aspect_ratio | Combo | 1:1 | One of: 1:1, 16:9, 9:16, 4:3, 3:4, 2:1, 1:2, auto (optional) |
| resolution | Combo | 1k | 1k (~1024px) or 2k (~2048px) (optional) |
| n | Int | 1 | Number of images to generate (1–4) (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Batched tensor (n, H, W, 3) of the generated images |

## Notes

- xAI returns time-limited URLs; the node downloads them immediately and converts to tensors.
- Batched output: connect to Preview Image to see all `n` results in one node.
- Async-enabled — concurrent Grok Image Generation nodes share the event loop.
- Generated URLs are not stored long-term by xAI ("download or process promptly" per their docs); the tensor output preserves the image locally.
