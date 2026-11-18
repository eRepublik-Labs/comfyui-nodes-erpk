<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.0 Flash Layers ComfyUI node. -->
<!-- ABOUTME: Splits one image into a clean base plus up to 16 images and alpha masks. -->

# Bytedance Seedream V5.0 Flash Layers

Splits one image into layers with ByteDance's Seedream V5.0 Flash layer decomposition. You get the scene with every separated object removed, plus up to 16 layers, each with its own mask.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| images | Image | -- | The image to decompose, as an IMAGE with one image (optional). Sent inline as base64, no upload. Takes precedence over image_url |
| image_url | String | (empty) | URL of the image to decompose. Needed unless images is connected |
| prompt | String | "" | Optional guidance, for example which objects to separate |
| resolution | Combo | "1k" | Output resolution tier: 1k, 1.5k or 2k |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| seed | Int | -1 | Cache control only, not sent to the API. -1 decomposes again every run; a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| base | IMAGE | The scene with every separated object removed |
| layers | IMAGE (list) | One RGB image per object, up to 16 |
| masks | MASK (list) | One alpha mask per layer: 1 where the object is, 0 where transparent |

## Notes

- **Pricing:** a flat $0.459 per run at every resolution tier
- **API Docs:** [Bytedance Seedream V5.0 Flash Layer Decomposition](https://wavespeed.ai/docs/docs-api/bytedance/seedream-v5.0-flash/layer-decomposition)
- **Layers are lists, not a batch.** Each layer can come back at its own size, so they cannot share one IMAGE batch. A node connected to `layers` or `masks` runs once per layer
- Layers are always requested as PNG, because JPEG would drop the transparency
