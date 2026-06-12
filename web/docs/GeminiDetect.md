<!-- ABOUTME: Help documentation for the Gemini Detect ComfyUI node. -->
<!-- ABOUTME: Detects objects in an image and emits their bounding boxes as ERPK regions. -->

# Gemini Detect

Detects objects in an image using Gemini's vision capabilities and emits their bounding boxes as regions. Wire the output into the Regional Prompt Builder's `regions` input to seed a layout from an existing image.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | - | Image to detect objects in (single frame) |
| objects | String | "" | Objects to detect, one per line (e.g. "red car"). Leave empty to detect all prominent objects. |
| client | GEMINI_API_CLIENT | - | Gemini API client (optional if API key is configured in Settings) |
| model | Combo | gemini-3.5-flash | Model to use for detection (optional) |
| temperature | Float | 0.0 | Lower = more deterministic detection, 0.0-2.0 (optional) |
| max_objects | Int | 20 | Maximum number of regions to return, 1-100 (optional) |
| seed | Int | -1 | Seed for reproducible detection; randomizes by default |

## Output

| Output | Type | Description |
|--------|------|-------------|
| regions | ERPK_REGIONS | Detected regions as JSON for the Regional Prompt Builder's `regions` input |

## Notes

- Regions are appended **after** any canvas-drawn regions on the builder, so `desc_N`/`ref_N` socket overrides still bind only the canvas regions.
- Detection runs in structured-output (JSON) mode, so the parse path is reliable regardless of the selected model.
- Degenerate boxes (width or height at or below 0.5% of the frame) are dropped; coordinates are clamped into the frame.
- `max_objects` keeps the first N detections returned by the model, not the largest N.
- Default temperature is 0.0 for factual, repeatable detection.
