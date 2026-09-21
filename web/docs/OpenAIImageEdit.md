<!-- ABOUTME: Help documentation for the OpenAI Image Edit ComfyUI node. -->
<!-- ABOUTME: Edits existing images using OpenAI's image editing API with optional masking. -->

# OpenAI Image Edit

Edits existing images based on text prompts using OpenAI's image editing API. Supports optional masking for targeted inpainting.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | Image | — | Input image to edit |
| prompt | String | (empty) | Description of how to modify the image |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is configured in Settings) |
| mask | Mask | — | Areas to edit: white=edit, black=keep (optional). Enables inpainting |
| model | Combo | gpt-image-2 | Editing model: gpt-image-2.5-sunburst, gpt-image-2.5-flare, gpt-image-2, gpt-image-1.5, gpt-image-1, gpt-image-1-mini (optional) |
| size | String | 1024x1024 | Output size as WIDTHxHEIGHT or `auto` (optional). gpt-image-1.5 / 1 / 1-mini: 1024x1024, 1024x1536, 1536x1024, auto only. gpt-image-2 and 2.5: arbitrary sizes, edges divisible by 16, aspect ratio 1:3 to 3:1, 655,360 to 8,294,400 pixels, max edge 3840 |
| quality | Combo | auto | Image quality: auto, low, medium, high, xhigh, max (optional). gpt-image models only; xhigh/max on GPT Image 2.5 only (clamped to high elsewhere) |
| moderation | Combo | auto | Content filter strictness: auto or low (optional). See Notes |
| n | Int | 1 | Number of images to generate (optional). Range: 1–10 |
| background | Combo | auto | auto, transparent, opaque (optional). GPT Image models only |
| input_fidelity | Combo | auto | auto, high, low (optional). Sent only to gpt-image-1.5 / 1 / 1-mini; gpt-image-2 and the 2.5 models reject it, so it is dropped there |
| seed | Int | -1 | Cache control only, not sent to the API. -1 randomizes (re-runs every queue); a fixed value reuses the cached result |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Edited image tensor |

## Notes

- **`moderation` is a request, not a guarantee**: `low` asks OpenAI for less restrictive filtering. Measured on 2026-09-17, gpt-image-1.5 and both GPT Image 2.5 models honour it for artistic nudity while gpt-image-2 does not, and gpt-image-2.5-sunburst was inconsistent across identical requests. Graphic violence is refused at both levels on every model. OpenAI documents no per-model difference, so this can change without notice.
- **Refusals are legible**: a blocked request reports whether the prompt or the generated image was refused, plus the categories involved. A prompt-stage refusal is often fixable by rewording; an output-stage one usually is not.
- **System instructions do not apply**: the images endpoint accepts only a prompt, with no system or instructions field. Connecting an OpenAI System Instruction node upstream has no effect here; fold that guidance into the prompt. The OpenAI Image via Responses node is the one image path that does honour it.
- **Sizes were measured live on 2026-09-21**: 512x512 and 256x256 are rejected by every model this node offers (they are dall-e-2 sizes), `auto` works everywhere, and 1536x864 works on gpt-image-2 and the 2.5 models but not on the 1.x models. Sizes outside the gpt-image-2 envelope are rejected before the request is sent.
- Without a mask, the model edits the entire image based on the prompt
- With a mask, only white areas are modified (inpainting mode)
- The mask is converted to an alpha channel internally — white regions become transparent for the API
