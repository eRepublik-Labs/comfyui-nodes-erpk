<!-- ABOUTME: Help documentation for the SHARP Predict ComfyUI node. -->
<!-- ABOUTME: Converts a single image to a 3D Gaussian splat using Apple's SHARP model. -->

# SHARP Predict (Image to 3D Gaussian)

Converts a single photograph into a 3D Gaussian splat (.ply file) using Apple's SHARP model. The output can be rendered from novel viewpoints using the SHARP Render nodes.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input photograph |
| focal_length_px | Float | 0.0 | Focal length in pixels (optional). 0 = auto-estimate from image width. Range: 0.0–10000.0 |
| output_dir | String | (empty) | Output directory for .ply file (optional). Empty = ComfyUI output folder |
| filename_prefix | String | sharp | Prefix for output filename (optional) |
| device | Combo | auto | Processing device (optional). Options: auto, cuda, mps, cpu |

## Output

| Output | Type | Description |
|--------|------|-------------|
| ply_path | String | Path to the saved .ply file |
| gaussians | SHARP_GAUSSIANS | 3D Gaussian splat data for rendering |

## Notes

- Requires SHARP: `pip install git+https://github.com/apple/ml-sharp.git`
- Model weights are downloaded from Apple's CDN on first use (~500MB)
- Processes internally at 1536x1536 resolution
- Output .ply files are auto-numbered (sharp_00001.ply, sharp_00002.ply, etc.)
- For best results, use well-lit photographs with a clear subject
