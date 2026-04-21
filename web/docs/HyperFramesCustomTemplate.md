<!-- ABOUTME: Help documentation for the HyperFrames Custom Template ComfyUI node. -->
<!-- ABOUTME: Renders a user-provided HyperFrames HTML composition with optional image substitution. -->

# HyperFrames Custom Template

Render a video from a user-provided HyperFrames HTML composition. Ideal when the Simple Composer is not flexible enough — you supply the full HTML (including GSAP timeline script) and optionally pipe images through `{{image_N}}` placeholders.

## Prerequisites

- **Node.js >= 22** on PATH (install from https://nodejs.org/)
- **FFmpeg** on PATH (install from https://ffmpeg.org/)
- The `hyperframes` npm package is auto-installed globally on first use if it is missing but Node.js is present.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| html_template | String (multiline) | "" | Full HyperFrames HTML. Use `{{image_1}}`, `{{image_2}}`, ... as src placeholders for input images (1-indexed). |
| images | IMAGE | - | Optional image batch. Each frame is written as `image_1.png`, `image_2.png`, ... next to the HTML. |
| output_format | Combo | mp4 | Output container: `mp4`, `mov`, or `webm`. |
| fps | Combo | 30 | Frames per second: `24`, `30`, or `60`. |
| quality | Combo | standard | `draft`, `standard`, or `high`. |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_url | String | `/view?` URL for the rendered video in ComfyUI's temp directory. |

## HTML schema requirements

Your template must follow the HyperFrames schema:

- Root is any `<div>` with `data-composition-id`, `data-start="0"`, `data-width`, `data-height`.
- Every timed visible element (`<img>`, `<div>`, text overlays) needs `class="clip"`, `data-start`, and `data-duration`.
- Use `data-track-index` (higher = front) — the deprecated `data-layer` is ignored.
- `<video>` elements must be `muted`. Background audio goes in separate `<audio>` elements with `data-volume` between 0 and 1.
- Register a GSAP timeline to `window.__timelines["<composition-id>"]`. The key must match `data-composition-id` exactly.
- Extend the timeline to the full composition length with `tl.set({}, {}, DURATION)` — rendered length is `tl.duration()`, not the sum of element durations.
- Load GSAP from CDN: `<script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>`.
- No `Math.random()`, `Date.now()`, `setTimeout`, `fetch()`, or `async/await` in the GSAP setup — renders must be deterministic.

## Notes

- Placeholders that have no matching image are left untouched in the template (useful for referencing external URLs directly).
- The first render can be slow because it may install the `hyperframes` npm package globally.
- Output plugs directly into the `Preview Anything` utility node for in-graph playback and download.
