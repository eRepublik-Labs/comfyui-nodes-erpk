<!-- ABOUTME: Help documentation for the Bytedance Seedream V5.5 Layers ComfyUI node. -->
<!-- ABOUTME: Splits one image into a clean base plus one image and alpha mask per object. -->

# Bytedance Seedream V5.5 Layers

Splits one image into layers with ByteDance's Seedream V5.5 layer decomposition. You get the scene with every separated object removed, plus one image and mask per object.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| images | Image | -- | The image to decompose, as an IMAGE with one image (optional). Sent inline as base64, no upload. Takes precedence over image_url |
| image_url | String | (empty) | URL of the image to decompose. Needed unless images is connected |
| prompt | String | "" | Optional guidance, for example which objects to separate |
| resolution | Combo | "1k" | Output resolution tier: 1k, 1.5k or 2k |
| max_images | Int | 10 | Most images to return, 2 to 100, counting the base plus the layers. This number sets the price |
| client | WAVESPEED_AI_API_CLIENT | -- | WaveSpeed API client (optional if API key is configured in Settings) |
| seed | Int | -1 | Cache control only, not sent to the API. -1 decomposes again every run; a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| base | IMAGE | The scene with every separated object removed |
| layers | IMAGE (list) | One RGB image per object |
| masks | MASK (list) | One alpha mask per layer: 1 where the object is, 0 where transparent |

## Notes

- **Pricing:** `max_images` x $0.02 at 1k or 1.5k, `max_images` x $0.035 at 2k. You pay for `max_images` even when fewer images return, so the default of 10 costs $0.20 at 1k. Lower it when the image holds few objects
- **API Docs:** [Bytedance Seedream V5.5 Layer Decomposition](https://wavespeed.ai/docs/docs-api/bytedance/seedream-v5.5/layer-decomposition)
- **Layers are lists, not a batch.** Each layer can come back at its own size, so they cannot share one IMAGE batch. A node connected to `layers` or `masks` runs once per layer
- Layers are always requested as PNG, because JPEG would drop the transparency
- Objects past the `max_images` limit stay in `base`. A three-object scene run with `max_images` 3 returned two layers and left the third object in the base
