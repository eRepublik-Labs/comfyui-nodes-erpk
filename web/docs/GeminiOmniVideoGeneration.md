<!-- ABOUTME: Help documentation for the Gemini Omni Video Generation ComfyUI node. -->
<!-- ABOUTME: Generates short 360p-4k video from a prompt or a start image via Gemini Omni Flash. -->

# Gemini Omni Video Generation

Generates 3-10 second video at 24 FPS, 360p to 4k, using Gemini Omni Flash 1.1 (`gemini-omni-1.1-flash`). Connect an image to animate it (image-to-video) instead of generating from text alone.

Unlike the Veo nodes, this model is reached through Google's Interactions API and returns the video directly rather than through a long-running operation, so a generation completes in one call with no polling.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | What the video should show |
| client | GEMINI_API_CLIENT | - | Gemini API client. Optional when the key is in ComfyUI Settings |
| image | Image | - | Optional start image. Connecting one switches the model to image-to-video (optional) |
| aspect_ratio | Combo | 16:9 | Video aspect ratio: 16:9 (landscape) or 9:16 (portrait) (optional) |
| output_directory | String | "" | Directory to save video. Empty uses ComfyUI output folder (optional) |
| seed | Int | -1 | Cache control only — never sent to the API. Range: -1 to 4294967295 (optional) |
| resolution | Combo | 720p | Output resolution: 360p, 720p, 1080p or 4k. 1080p and 4k are upscaled by Google and need a stored interaction, so the node downloads, then deletes, the file (optional) |

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
- **Duration** — the model picks 3-10s; output is always 24 FPS

## Large outputs

1080p and 4k videos exceed the 4MB inline response limit, so the node asks for URI delivery at those resolutions, waits for the Files API to mark the video ACTIVE (up to 10 minutes) and downloads it. 360p and 720p come back inline in the same call. The generation call itself gets at least a 15-minute timeout, since a 1080p or 4k render can take longer than the 5-minute default.

## Other limitations

- Interpolation (generating between a first and last frame) is not exposed by this node
- Audio reference upload is not supported in the current API version
- Reasoning across multiple input videos is not supported
- To generate from reference images, use Gemini Omni Reference to Video
- All output carries a SynthID watermark

## Pricing

$1.50 per 1M input tokens, and roughly $0.10 per second of generated video at 720p. Google has not published separate 1080p or 4k rates on the pricing page this node was checked against.
