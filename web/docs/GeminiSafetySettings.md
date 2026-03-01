<!-- ABOUTME: Help documentation for the Gemini Safety Settings ComfyUI node. -->
<!-- ABOUTME: Configures content safety filters for Gemini API requests. -->

# Gemini Safety Settings

Configures content safety filters for Gemini API requests. Choose from presets or define custom thresholds per category.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | GEMINI_API_CLIENT | - | Gemini API client to configure |
| preset | Combo | balanced | Safety preset: balanced, strict, permissive, or custom (optional) |
| harassment | Combo | medium | Harassment content threshold: none, low, medium, high. Only used with custom preset (optional) |
| hate_speech | Combo | medium | Hate speech threshold: none, low, medium, high. Only used with custom preset (optional) |
| sexually_explicit | Combo | medium | Sexually explicit content threshold: none, low, medium, high. Only used with custom preset (optional) |
| dangerous_content | Combo | medium | Dangerous content threshold: none, low, medium, high. Only used with custom preset (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| client | GEMINI_API_CLIENT | Client with updated safety settings |

## Notes

- **strict**: Blocks low severity and above for all categories (safest)
- **balanced**: Blocks medium severity and above (recommended default)
- **permissive**: Blocks only high severity content
- **custom**: Set individual thresholds per category
- Place this node between Gemini API Config and generation nodes in your workflow
