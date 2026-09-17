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
| size | Combo | 1024x1024 | Output image size (optional). Options: 1024x1024, 1024x1536, 1536x1024, 512x512, 256x256 |
| quality | Combo | auto | Image quality: auto, low, medium, high, xhigh, max (optional). gpt-image models only; xhigh/max on GPT Image 2.5 only (clamped to high elsewhere) |
| n | Int | 1 | Number of images to generate (optional). Range: 1–4 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Edited image tensor |

## Notes

- **`moderation` is a request, not a guarantee**: `low` asks OpenAI for less restrictive filtering. Measured on 2026-09-17, gpt-image-1.5 and both GPT Image 2.5 models honour it for artistic nudity while gpt-image-2 does not, and gpt-image-2.5-sunburst was inconsistent across identical requests. Graphic violence is refused at both levels on every model. OpenAI documents no per-model difference, so this can change without notice.
- **Refusals are legible**: a blocked request reports whether the prompt or the generated image was refused, plus the categories involved. A prompt-stage refusal is often fixable by rewording; an output-stage one usually is not.
- **System instructions do not apply**: the images endpoint accepts only a prompt, with no system or instructions field. Connecting an OpenAI System Instruction node upstream has no effect here; fold that guidance into the prompt. The OpenAI Image via Responses node is the one image path that does honour it.
- Without a mask, the model edits the entire image based on the prompt
- With a mask, only white areas are modified (inpainting mode)
- The mask is converted to an alpha channel internally — white regions become transparent for the API
