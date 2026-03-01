<!-- ABOUTME: Help documentation for the SHARP Render Views ComfyUI node. -->
<!-- ABOUTME: Renders novel views from a SHARP 3D Gaussian splat. -->

# SHARP Render Views

Renders novel views from a SHARP Gaussian splat (.ply file). Produces a batch of images from different viewpoints around the scene. Requires CUDA.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| ply_path | String | — | Path to .ply file (connect from SHARP Predict) |
| num_views | Int | 8 | Number of views to render around the scene. Range: 1–64 |
| resolution | Int | 512 | Output image resolution (optional). Range: 256–2048 |
| max_disparity | Float | 0.08 | Maximum camera disparity for view synthesis (optional). Range: 0.01–0.5 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| images | Image | Batch of rendered view images |

## Notes

- Requires CUDA — cannot run on CPU or MPS
- Requires gsplat: `pip install gsplat`
- Higher max_disparity produces wider camera movement between views
- Output images are square at the specified resolution
- Connect to Preview Image or Save Image nodes to view results
