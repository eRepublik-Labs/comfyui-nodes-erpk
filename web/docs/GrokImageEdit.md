<!-- ABOUTME: Help documentation for the Grok Image Edit ComfyUI node. -->
<!-- ABOUTME: Single or multi-image editing (up to 5 sources) via xAI's grok-imagine-image-2.0. -->

# Grok Image Edit

Edits one or more input images using a text prompt. Pass a batched IMAGE tensor with up to 5 frames for multi-image editing (xAI's documented cap for grok-imagine-image-2.0).

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | — | Source image(s). Batched tensor allowed — up to 5 frames used (xAI cap); extra frames are dropped |
| prompt | String | (empty) | Editing instructions |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-imagine-image-2.0 | Image model. Only option: grok-imagine-image-2.0 (optional) |
| aspect_ratio | Combo | auto | "auto" follows the first source image; otherwise one of 1:1, 16:9, 9:16, 4:3, 3:4, 2:1, 1:2, 3:2, 2:3, 19.5:9, 9:19.5, 20:9, 9:20 (optional) |
| resolution | Combo | auto | auto, 1k (~1024px) or 2k (~2048px). "auto" sends nothing and lets xAI choose (optional) |
| n | Int | 1 | Number of edited variations, 1-10. Each one is billed (optional) |
| quality | Combo | auto | auto, low or medium. "auto" sends nothing and lets xAI choose (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image tensor (a batch of n images) |

## Notes

- xAI requires images as `application/json` data URIs (not multipart). This node converts the input tensor to base64 JPEG data URIs automatically, downscaling if needed so all sources fit one request (the xai-sdk sends at most 20 MiB).
- Multi-turn editing: chain Edit nodes by feeding each output into the next Edit's `image` input.
- The first frame of a batch is the primary source; additional frames act as references in the order received. Address them in the prompt as `<IMAGE_0>`, `<IMAGE_1>`, and so on.
- Async-enabled — concurrent Grok Image Edit nodes share the event loop.
