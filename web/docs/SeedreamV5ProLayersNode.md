<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Pro Layers ComfyUI node. -->
<!-- ABOUTME: Splits one image into a clean base plus one image and alpha mask per object. -->

# Bytedance Seedream V5.0 Pro Layers

Splits one image into layers with ByteDance's Seedream V5.0 Pro layer decomposition. You get the scene with every separated object removed, plus one image and mask per object. Hidden parts of an object are regenerated, so a layer is the whole object, not just its visible part.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| images | Image | -- | The image to decompose, as an IMAGE with one image (optional). Sent inline as base64, no upload. Takes precedence over image_url |
| image_url | String | (empty) | URL of the image to decompose. Needed unless images is connected |
| prompt | String | "" | Optional guidance, for example which objects to separate |
| resolution | Combo | "1k" | Output resolution tier: 1k, 1.5k or 2k |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| prompt_optimization_mode | Combo | "standard" | The model rewrites the prompt first. fast is quicker but follows long prompts less closely (optional) |
| seed | Int | -1 | Cache control only, not sent to the API. -1 decomposes again every run; a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| base | IMAGE | The scene with every separated object removed |
| layers | IMAGE (list) | One RGB image per object |
| masks | MASK (list) | One alpha mask per layer: 1 where the object is, 0 where transparent. Same convention as Qwen Image Layered |

## Notes

- **Pricing:** $0.765 per run at 1k or 1.5k, $1.53 at 2k. That is about 17 times the price of a Seedream Pro image
- **API Docs:** [Bytedance Seedream V5.0 Pro Layer Decomposition](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedream-v5.0-pro-layer-decomposition)
- **Layers are lists, not a batch.** Each layer is cropped to its object and comes back at its own size, so they cannot share one IMAGE batch. A node connected to `layers` or `masks` runs once per layer
- **No positions come back.** The API does not say where each layer sat in the original, so the layers cannot be placed back on `base` automatically
- The number of layers depends on the image: a scene with two objects returned two layers when tested on 2026-09-22
- Layers are always requested as PNG, because JPEG would drop the transparency
