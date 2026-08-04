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
| model | Combo | (inherit from client) | Override the client's model for this vision call (optional). Options: (inherit from client), claude-sonnet-5, claude-opus-5, claude-opus-4-8, claude-fable-5, claude-opus-4-7, claude-sonnet-4-6, claude-opus-4-6, claude-haiku-4-5-20251001, claude-sonnet-4-5-20250929 |
| additional_images | IMAGE | (none) | Additional images to analyze, up to 19 more for 20 total (optional) |
| detail_level | Combo | high | Level of detail in analysis (optional). Options: low, medium, high |
| max_tokens | Int | 2048 | Maximum length of analysis (optional). Min: 256, Max: 4096, Step: 128 |
| seed | Int | -1 | Cache control. A fixed seed reuses the previous result; -1 re-runs every queue (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| analysis | String | Detailed image analysis text |

## Notes

- Supports up to 20 images total (1 primary + 19 additional)
- Oversized images are automatically resized (max 8000px dimension)
- Detail levels control how thorough the analysis is: low = concise, high = comprehensive
- Use cases: image captioning, prompt reverse-engineering, quality assessment, data extraction
- Caching follows the seed: a fixed seed reuses the analysis you already paid for, while -1 (randomize) re-runs on every queue
- Opus 4.7 and later accept 2576px images, against 1568px on earlier models
