<!-- ABOUTME: Help documentation for the HyperFrames Simple Composer ComfyUI node. -->
<!-- ABOUTME: Composes a video from a batch of images, captions, and optional audio via local subprocess render. -->

# HyperFrames Simple Composer

Compose a video from a batch of scene images with optional captions, background audio, and scene transitions. Each image becomes a full-frame scene in the rendered video. Rendering runs locally via the `hyperframes` CLI — no HTTP API or remote service involved.

## Prerequisites

- **Node.js >= 22** on PATH (install from https://nodejs.org/)
- **FFmpeg** on PATH (install from https://ffmpeg.org/)
- The `hyperframes` npm package is auto-installed globally on first use if it is missing but Node.js is present.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| images | IMAGE | - | Scene images as a batch. Each image becomes one scene. |
| captions | String | "" | One caption per scene, separated by newlines. Leave blank for none. |
| duration_per_scene | Int | 3 | Seconds each scene is displayed (1-30). |
| stage_width | Int | 1920 | Composition width in pixels (320-4096). |
| stage_height | Int | 1080 | Composition height in pixels (320-4096). |
| audio_url | String | "" | Optional URL or local path to a background audio file (mp3, wav, m4a). |
| transition | Combo | fade | Scene transition style: `cut`, `fade`, or `crossfade`. |
| output_format | Combo | mp4 | Output container: `mp4`, `mov` (ProRes, alpha), `webm` (VP9, alpha). |
| fps | Combo | 30 | Frames per second: `24`, `30`, or `60`. |
| quality | Combo | standard | `draft` (fast, CRF 28), `standard` (CRF 18), `high` (best, CRF 15, slow). |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | `/view?` URL for the rendered video inside ComfyUI's temp directory. Plug this into a Preview Anything node to watch the result, or pass it to a downstream save node. |

## Notes

- Captions are aligned 1:1 with scenes. Fewer caption lines than scenes leaves trailing scenes uncaptioned; extra lines are ignored.
- Total duration = `number_of_scenes * duration_per_scene`. The GSAP timeline is explicitly extended so the render does not cut off early even if the last animation ends sooner.
- `transition="cut"` disables fade animations for instant scene changes.
- Audio URLs are fetched directly by the renderer during composition — pass only trusted sources.
- The first render can be slow because it may install the `hyperframes` npm package globally.
- Output plugs directly into the `Preview Anything` utility node for in-graph playback and download.
