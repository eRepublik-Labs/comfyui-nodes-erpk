<!-- ABOUTME: Help documentation for the OpenAI Image Generation ComfyUI node. -->
<!-- ABOUTME: Generates images using OpenAI's DALL-E and GPT-Image models. -->

# OpenAI Image Generation

Generates images using OpenAI's image generation models including GPT-Image 1.5, GPT-Image 1, and DALL-E 3.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Description of the image to generate |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if API key is configured in Settings) |
| model | Combo | gpt-image-2 | Image model: gpt-image-2, gpt-image-2.5-sunburst, gpt-image-2.5-flare, gpt-image-1.5, gpt-image-1, gpt-image-1-mini (optional) |
| size | Combo | 1024x1024 | Size preset or Custom (optional). Presets: auto, 1024x1024, 1024x1536, 1536x1024, 2048x2048, 2048x1152, 1152x2048, 3840x2160, 2160x3840. GPT Image 1.x: 1024-series and auto. gpt-image-2 and 2.5: any Custom size with edges divisible by 16, aspect ratio 1:3 to 3:1, 655,360 to 8,294,400 pixels, max edge 3840; above 2560x1440 is experimental per OpenAI. DALL-E 3 via Custom: 1792x1024, 1024x1792. DALL-E 2 via Custom: 256x256, 512x512 |
| custom_width | Int | 1024 | Width when size is Custom (optional). 256 to 3840, step 16 |
| custom_height | Int | 1024 | Height when size is Custom (optional). 256 to 3840, step 16 |
| quality | Combo | auto | Image quality (optional). gpt-image: low/medium/high/auto; xhigh/max on GPT Image 2.5 only (clamped to high elsewhere). dall-e-3: hd/standard |
| background | Combo | auto | Background type: auto, transparent, opaque (optional). gpt-image models only |
| n | Int | 1 | Number of images to generate (optional). Range: 1–4. DALL-E 3 only supports 1 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Generated image tensor |
| revised_prompt | String | The prompt as revised by the model (may differ from input) |

## Notes

- **`moderation` is a request, not a guarantee**: `low` asks OpenAI for less restrictive filtering. Measured on 2026-09-17, gpt-image-1.5 and both GPT Image 2.5 models honour it for artistic nudity while gpt-image-2 does not, and gpt-image-2.5-sunburst was inconsistent across identical requests. Graphic violence is refused at both levels on every model. OpenAI documents no per-model difference, so this can change without notice.
- **Refusals are legible**: a blocked request reports whether the prompt or the generated image was refused, plus the categories involved. A prompt-stage refusal is often fixable by rewording; an output-stage one usually is not.
- **System instructions do not apply**: the images endpoint accepts only a prompt, with no system or instructions field. Connecting an OpenAI System Instruction node upstream has no effect here; fold that guidance into the prompt. The OpenAI Image via Responses node is the one image path that does honour it.
- GPT-Image 1.5 is the latest and highest quality model
- DALL-E 3 supports 1792x1024 and 1024x1792 sizes; GPT-Image models do not
- Workflows saved before custom_width / custom_height existed load unchanged; a typed size that is not a preset is restored as Custom with the dimensions filled in
- Use "transparent" background for images with alpha channel (gpt-image models only)
- The revised_prompt output shows how the model interpreted your prompt
