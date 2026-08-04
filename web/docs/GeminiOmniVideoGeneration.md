<!-- ABOUTME: Help documentation for the Gemini Omni Video Generation ComfyUI node. -->
<!-- ABOUTME: Generates short 720p video from a prompt or a start image via Gemini Omni Flash. -->

# Gemini Omni Video Generation

Generates 3-10 second video at 720p / 24 FPS using Gemini Omni Flash. Connect an image to animate it (image-to-video) instead of generating from text alone.

Unlike the Veo nodes, this model is reached through Google's Interactions API and returns the video directly rather than through a long-running operation, so a generation completes in one call with no polling.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | What the video should show |
| client | GEMINI_API_CLIENT | - | Gemini API client. Optional when the key is in ComfyUI Settings |
| image | Image | - | Optional start image. Connecting one switches the model to image-to-video (optional) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 (landscape) or 9:16 (portrait) (optional) |
| output_directory | String | "" | Directory to save video. Empty uses ComfyUI output folder (optional) |
| seed | Int | 0 | Cache control only — never sent to the API. Range: -1 to 4294967295 (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| video_path | String | File path to the generated .mp4 video |

## The seed does not reach the API

Omni Flash accepts no seed, so this widget exists purely to control ComfyUI's cache. A **fixed** seed lets the graph reuse the video you already paid for; **-1** (randomize) marks the node dirty and generates again on every queue. Changing it does not change what the model produces — only whether it runs.

## Unsupported parameters

The model rejects several knobs the other Gemini nodes accept, so this node does not expose them:

- **Negative prompts** — state exclusions inline instead, e.g. "Do not show text on screen"
- **System instructions, temperature, top_p, stop sequences**
- **Duration and resolution** — output is fixed at 3-10s, 720p, 24 FPS

## Other limitations

- Video extension and interpolation (generating between a first and last frame) are not supported
- Audio reference upload is not supported in the current API version
- Reasoning across multiple input videos is not supported
- Editing uploaded videos is unavailable in the EEA, Switzerland and the UK; editing model-generated video still works there
- All output carries a SynthID watermark

## Pricing

$1.50 per 1M input tokens, and roughly $0.10 per second of generated video.
