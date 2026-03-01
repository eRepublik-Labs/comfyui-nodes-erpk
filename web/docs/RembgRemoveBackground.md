<!-- ABOUTME: Help documentation for the Remove Background (rembg) ComfyUI node. -->
<!-- ABOUTME: Removes backgrounds using the rembg library with 14+ ONNX models. -->

# Remove Background (rembg)

Removes backgrounds using the rembg library with ONNX Runtime inference. Supports 14+ models optimized for different use cases including general purpose, human segmentation, anime, and clothing parsing.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image(s) |
| model | Combo | u2net | Model to use. Options: u2net, u2netp, u2net_human_seg, u2net_cloth_seg, silueta, isnet-general-use, isnet-anime, sam, birefnet-general, birefnet-general-lite, birefnet-portrait, birefnet-dis, birefnet-hrsod, birefnet-cod, birefnet-massive |
| alpha_matting | Boolean | False | Enable alpha matting for cleaner edges (optional) |
| alpha_matting_foreground_threshold | Int | 240 | Foreground threshold for alpha matting (optional). Range: 0–255 |
| alpha_matting_background_threshold | Int | 10 | Background threshold for alpha matting (optional). Range: 0–255 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Image with background removed (RGBA) |
| mask | Mask | Foreground segmentation mask |

## Notes

- Requires `rembg` package: `pip install rembg[gpu]`
- u2net is the default general-purpose model; u2netp is lighter/faster
- isnet-anime is specialized for anime character extraction
- u2net_cloth_seg extracts clothing regions specifically
- Alpha matting produces smoother edges but is slower
