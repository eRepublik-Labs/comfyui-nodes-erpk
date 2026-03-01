<!-- ABOUTME: Help documentation for the OpenAI Image Generation ComfyUI node. -->
<!-- ABOUTME: Generates images using OpenAI's DALL-E and GPT-Image models. -->

# OpenAI Image Generation

Generates images using OpenAI's image generation models including GPT-Image 1.5, GPT-Image 1, and DALL-E 3.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | (empty) | Description of the image to generate |
| client | OPENAI_API_CLIENT | — | OpenAI API client (optional if using api_key or Settings) |
| model | Combo | gpt-image-1.5 | Image model: gpt-image-1.5, gpt-image-1, gpt-image-1-mini, dall-e-3 (optional) |
| size | Combo | 1024x1024 | Image size (optional). Options: 1024x1024, 1024x1536, 1536x1024, 512x512, 256x256, 1792x1024, 1024x1792 |
| quality | Combo | auto | Image quality (optional). gpt-image: low/medium/high/auto. dall-e-3: hd/standard |
| background | Combo | auto | Background type: auto, transparent, opaque (optional). gpt-image models only |
| n | Int | 1 | Number of images to generate (optional). Range: 1–4. DALL-E 3 only supports 1 |
| api_key | String | (empty) | OpenAI API key (optional). Only needed if not using client input |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Generated image tensor |
| revised_prompt | String | The prompt as revised by the model (may differ from input) |

## Notes

- GPT-Image 1.5 is the latest and highest quality model
- DALL-E 3 supports 1792x1024 and 1024x1792 sizes; GPT-Image models do not
- Use "transparent" background for images with alpha channel (gpt-image models only)
- The revised_prompt output shows how the model interpreted your prompt
