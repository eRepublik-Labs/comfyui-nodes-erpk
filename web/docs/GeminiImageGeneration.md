<!-- ABOUTME: Help documentation for the Gemini Image Generation ComfyUI node. -->
<!-- ABOUTME: Generates images from text descriptions using Gemini's image generation models. -->

# Gemini Image Generation

Generates images from text descriptions using Gemini's image generation models. Supports multiple aspect ratios, resolutions, and optional text descriptions.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String | "" | Description of the image to generate |
| client | GEMINI_API_CLIENT | - | Gemini API client (optional, uses API key from config) |
| model | Combo | gemini-3.1-flash-image | Image model: gemini-3.1-flash-image, gemini-3.1-flash-lite-image, gemini-3-pro-image (optional) |
| temperature | Float | 1.0 | Creativity level, 0.0-2.0 (optional) |
| aspect_ratio | Combo | default | Image aspect ratio: default, 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9. 3.1 Flash Lite has no 1:4, 4:1, 1:8 or 8:1 and uses the closest supported ratio (optional) |
| image_size | Combo | default | Resolution: default, 0.5K, 1K, 2K, 4K. 3.1 Flash takes 0.5K-4K, 3 Pro 1K-4K, 3.1 Flash Lite 1K only; an unsupported size uses the model's smallest size (optional) |
| response_modalities | Combo | IMAGE | IMAGE (image only) or TEXT+IMAGE (image + text description) (optional) |
| enable_google_search | Boolean | false | Enable Google Search grounding on 3.1 Flash and 3 Pro; ignored on 3.1 Flash Lite, which does not support it (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| image | IMAGE | Generated image tensor |
| description | String | Text description (only populated when response_modalities is TEXT+IMAGE) |

## Notes

- 3.1 Flash supports all 14 aspect ratios and resolutions from 0.5K to 4K
- 3 Pro supports resolutions from 1K to 4K
- 3.1 Flash Lite outputs 1K only, has 10 aspect ratios (no 1:4, 4:1, 1:8, 8:1) and no Google Search grounding
- API key resolved from ComfyUI Settings or config.ini — connect a `client` from Gemini API Config only when you need shared safety/system-instruction state across nodes
