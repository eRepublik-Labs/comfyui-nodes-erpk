<!-- ABOUTME: Help documentation for the Remove Background (InSPyReNet) ComfyUI node. -->
<!-- ABOUTME: Removes backgrounds using InSPyReNet via transparent-background. -->

# Remove Background (InSPyReNet)

Removes backgrounds using InSPyReNet via the transparent-background library. High-resolution salient object detection with optional TorchScript JIT compilation for faster inference. MIT licensed.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image(s) |
| torchscript_jit | Boolean | False | Enable TorchScript JIT for faster inference and lower memory (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Image with background removed (RGBA) |
| mask | Mask | Foreground segmentation mask |

## Notes

- Requires `transparent-background` package: `pip install transparent-background`
- JIT compilation adds startup overhead but speeds up subsequent inference
- Model is cached between runs — only reloaded when JIT setting changes
