<!-- ABOUTME: Help documentation for the Claude Vision Analysis ComfyUI node. -->
<!-- ABOUTME: Analyzes images using Claude's multimodal vision capabilities. -->

# Claude Vision Analysis

Analyzes images using Claude's multimodal vision capabilities. Supports single or batch images with configurable detail levels.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| image | IMAGE | (required) | Primary image to analyze (ComfyUI tensor) |
| question | String (multiline) | Describe this image in detail. | Question or instruction about the image(s) |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| additional_images | IMAGE | (none) | Additional images to analyze, up to 19 more for 20 total (optional) |
| detail_level | Combo | high | Level of detail in analysis (optional). Options: low, medium, high |
| max_tokens | Int | 2048 | Maximum length of analysis (optional). Min: 256, Max: 4096, Step: 128 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| analysis | String | Detailed image analysis text |

## Notes

- Supports up to 20 images total (1 primary + 19 additional)
- Oversized images are automatically resized (max 8000px dimension)
- Detail levels control how thorough the analysis is: low = concise, high = comprehensive
- Use cases: image captioning, prompt reverse-engineering, quality assessment, data extraction
- Re-executes on every queue (not cached)
