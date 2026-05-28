<!-- ABOUTME: Help documentation for the Grok Image Edit ComfyUI node. -->
<!-- ABOUTME: Single or multi-image editing (up to 3 sources) via xAI's Grok image model. -->

# Grok Image Edit

Edits one or more input images using a text prompt. Pass a batched IMAGE tensor with up to 3 frames for multi-image editing (xAI's documented cap).

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | — | Source image(s). Batched tensor allowed — up to 3 frames used (xAI cap) |
| prompt | String | (empty) | Editing instructions |
| client | GROK_API_CLIENT | — | Grok API client (optional if API key is in Settings) |
| model | Combo | grok-imagine-image-quality | Image model (optional) |
| aspect_ratio | Combo | auto | "auto" preserves source ratio; otherwise one of 1:1, 16:9, 9:16, 4:3, 3:4, 2:1, 1:2 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image tensor |

## Notes

- xAI requires images as `application/json` data URIs (not multipart). This node converts the input tensor to base64 PNG data URIs automatically.
- Multi-turn editing: chain Edit nodes by feeding each output into the next Edit's `image` input.
- The first frame of a batch is the primary source; additional frames act as references in the order received.
- Async-enabled — concurrent Grok Image Edit nodes share the event loop.
