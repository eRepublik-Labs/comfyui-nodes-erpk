<!-- ABOUTME: Help documentation for the Gemini Image Edit ComfyUI node. -->
<!-- ABOUTME: Edits images using text prompts with Gemini's image generation models. -->

# Gemini Image Edit

Edits and modifies existing images using text prompts. Supports up to 14 reference images for multi-image editing tasks like style transfer and character consistency.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | - | Reference image(s) to edit. Use Batch Images node to combine multiple (up to 14). |
| prompt | String | "" | Describe the edit. Reference images by order, content, or role. |
| client | GEMINI_API_CLIENT | - | Gemini API client (optional, uses API key from config) |
| model | Combo | gemini-3.1-flash-image-preview | Image model: gemini-3.1-flash-image-preview, gemini-3-pro-image-preview, gemini-2.5-flash-image (optional) |
| temperature | Float | 1.0 | Creativity level, 0.0-2.0 (optional) |
| aspect_ratio | Combo | default | Image aspect ratio: default, 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9 (optional) |
| image_size | Combo | default | Resolution: default, 512px, 1K, 2K, 4K (optional) |
| response_modalities | Combo | IMAGE | IMAGE (image only) or TEXT+IMAGE (image + text description) (optional) |
| enable_google_search | Boolean | false | Enable Google Search grounding, Gemini 3 models only (optional) |
| additional_images | IMAGE | - | Additional reference images, combined with primary input up to 14 total (optional) |
| image_refs | ERPK_IMAGE_REFS | - | Ordered reference images from a Regional Prompt Builder; sent right after the primary image so the prompt's image numbers line up (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Edited image tensor |
| description | String | Text description (only populated when response_modalities is TEXT+IMAGE) |

## Notes

- Reference images in prompts by order ("the first image"), content ("the logo"), or role ("the style reference")
- Gemini 3 Pro supports up to 14 reference images (up to 6 objects, up to 5 humans for character consistency)
- Images are sent in order: primary image, then image_refs, then additional_images. The primary image is "the first image" in positional prompts
- API key resolved from ComfyUI Settings or config.ini — connect a `client` from Gemini API Config only when you need shared safety/system-instruction state across nodes
