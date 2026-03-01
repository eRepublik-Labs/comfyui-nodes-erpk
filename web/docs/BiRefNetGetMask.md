<!-- ABOUTME: Help documentation for the Get Mask (BiRefNet) ComfyUI node. -->
<!-- ABOUTME: Extracts segmentation mask using BiRefNet without removing background. -->

# Get Mask (BiRefNet)

Extracts a foreground segmentation mask using BiRefNet without producing a background-removed image. Useful when you only need the mask for compositing or other operations.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image(s) |
| variant | Combo | ZhengPeng7/BiRefNet | Model variant. Same 17 options as Remove Background (BiRefNet) |
| width | Int | 1024 | Processing width (optional). Range: 256–2560 |
| height | Int | 1024 | Processing height (optional). Range: 256–2560 |
| upscale_method | Combo | bilinear | Interpolation for resizing (optional) |
| device | Combo | auto | Processing device (optional). Auto selects CUDA > MPS > CPU |
| dtype | Combo | float32 | Data type (optional). float16 for lower VRAM usage |
| mask_threshold | Float | 0.0 | Soft threshold for noise removal (optional). Range: 0.0–1.0 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| mask | Mask | Foreground segmentation mask |

## Notes

- Shares the same model cache as Remove Background (BiRefNet) — no extra memory if both are used
- More efficient than the full removal node when you only need the mask
- Combine with other ComfyUI nodes for custom compositing workflows
