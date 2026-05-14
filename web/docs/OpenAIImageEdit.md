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
| model | Combo | gpt-image-1 | Editing model: gpt-image-1.5, gpt-image-1, gpt-image-1-mini (optional) |
| size | Combo | 1024x1024 | Output image size (optional). Options: 1024x1024, 1024x1536, 1536x1024, 512x512, 256x256 |
| quality | Combo | auto | Image quality: auto, low, medium, high (optional). gpt-image models only |
| n | Int | 1 | Number of images to generate (optional). Range: 1–4 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | Image | Edited image tensor |

## Notes

- Without a mask, the model edits the entire image based on the prompt
- With a mask, only white areas are modified (inpainting mode)
- The mask is converted to an alpha channel internally — white regions become transparent for the API
