<!-- ABOUTME: Help documentation for the SHARP Render Video ComfyUI node. -->
<!-- ABOUTME: Renders an orbit video from a SHARP 3D Gaussian splat. -->

# SHARP Render Video

Renders an orbit video from a SHARP Gaussian splat (.ply file). Produces both an MP4 video file and a batch of frame images. Requires CUDA.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| ply_path | String | — | Path to .ply file (connect from SHARP Predict) |
| num_frames | Int | 60 | Number of frames in the video (optional). Range: 10–300 |
| resolution | Int | 512 | Video resolution (optional). Range: 256–2048 |
| fps | Int | 30 | Frames per second (optional). Range: 15–60 |
| max_disparity | Float | 0.08 | Maximum camera disparity for view synthesis (optional). Range: 0.01–0.5 |
| output_dir | String | (empty) | Output directory (optional). Empty = ComfyUI output folder |
| filename_prefix | String | sharp_video | Prefix for output filename (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_path | String | Path to the saved .mp4 video file |
| frames | Image | Batch of all rendered frame images |

## Notes

- Requires CUDA — cannot run on CPU or MPS
- Requires gsplat and imageio: `pip install gsplat imageio`
- Videos are auto-numbered (sharp_video_00001.mp4, etc.)
- The frames output can be used for further processing in ComfyUI
- 60 frames at 30fps = 2 second orbit video
