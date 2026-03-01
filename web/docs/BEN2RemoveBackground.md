<!-- ABOUTME: Help documentation for the Remove Background (BEN2) ComfyUI node. -->
<!-- ABOUTME: Removes backgrounds using BEN2 with confidence-guided matting. -->

# Remove Background (BEN2)

Removes backgrounds using BEN2 (Background Erase Network 2). Uses confidence-guided matting for accurate alpha mattes at edges, especially effective for hair and fur. MIT licensed.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image(s) |
| refine_foreground | Boolean | False | Enable blur-fusion foreground refinement for cleaner edges (optional). Slower but better for hair/fur |
| device | Combo | auto | Processing device (optional). Auto selects CUDA > MPS > CPU |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Image with background removed (RGBA) |
| mask | Mask | Foreground segmentation mask |

## Notes

- Model weights are downloaded from HuggingFace (PramaLLC/BEN2) on first use
- Processes internally at 1024x1024 resolution
- Auto dtype: uses float16 on CUDA for efficiency, float32 on CPU
- Foreground refinement uses blur-fusion to reduce color bleeding at semi-transparent edges
