<!-- ABOUTME: Help documentation for the Remove Background (BiRefNet) ComfyUI node. -->
<!-- ABOUTME: Removes image backgrounds using BiRefNet with 17 model variants. -->

# Remove Background (BiRefNet)

Removes image backgrounds using BiRefNet via HuggingFace transformers. Supports 17 model variants for different use cases including general purpose, portrait, matting, and specialized detection. MIT licensed.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image(s) |
| variant | Combo | ZhengPeng7/BiRefNet | Model variant. 17 options including General, HR, Lite, Portrait, Matting, DIS, HRSOD, COD. Local models also listed if available |
| width | Int | 1024 | Processing width (optional). HR variants: 2048+, Lite variants: 512–1024. Range: 256–2560 |
| height | Int | 1024 | Processing height (optional). Same recommendations as width. Range: 256–2560 |
| upscale_method | Combo | bilinear | Interpolation for resizing (optional). Options: bilinear, bicubic, lanczos, nearest, nearest-exact, area |
| device | Combo | auto | Processing device (optional). Auto selects CUDA > MPS > CPU |
| dtype | Combo | float32 | Data type (optional). float16 uses ~50% less VRAM with slight quality differences |
| fill_background | Boolean | False | Fill background with solid color instead of transparent (optional) |
| background_color | String | #000000 | Hex color for background fill (optional). Only used when fill_background is enabled |
| mask_threshold | Float | 0.0 | Soft threshold for noise removal (optional). Try 0.004. Range: 0.0–1.0 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Image with background removed (RGBA or RGB with fill) |
| mask | Mask | Foreground segmentation mask |

## Notes

- Models are cached by variant/device/dtype — first run downloads from HuggingFace
- HR variants produce best results at 2048x2048 processing resolution
- Lite and 512x512 variants are fastest for real-time use
- Local models can be placed in ComfyUI's `models/BiRefNet/` directory (.safetensors or .pth)
- mask_threshold removes low-confidence noise while preserving gradient edges
