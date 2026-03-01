<!-- ABOUTME: Help documentation for the Claude Prompt Enhancer ComfyUI node. -->
<!-- ABOUTME: Enhances simple prompts with rich detail and artistic style for image generation. -->

# Claude Prompt Enhancer

Transforms simple prompts into detailed, styled descriptions for image generation. Supports 51 artistic styles across photography, digital art, traditional art, and more.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Simple prompt to enhance (e.g., "a cat") |
| style | Combo | photorealistic | Enhancement style to apply. 51 options including photorealistic, cinematic, anime, cyberpunk, oil_painting, etc. |
| detail_level | Combo | detailed | How much detail to add. Options: minimal, moderate, detailed, ultra-detailed |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| temperature | Float | 0.7 | Creativity level: 0.0 = focused, 1.0 = creative (optional). Min: 0.0, Max: 1.0, Step: 0.05 |
| max_tokens | Int | 1024 | Maximum length of enhanced prompt (optional). Min: 256, Max: 4096, Step: 128 |
| use_streaming | Boolean | False | Enable streaming (optional). May not display in real-time in ComfyUI |

## Output

| Output | Type | Description |
|--------|------|-------------|
| enhanced_prompt | String | Detailed, style-enhanced prompt text |

## Notes

- Each style has a custom system prompt guiding Claude to add style-specific details (lighting, composition, mood, etc.)
- Outputs only the enhanced prompt text with no preamble or explanation
- Connect the output directly to image generation nodes
- Re-executes on every queue (not cached) since results vary
- Style categories: Photography, Digital Art, Traditional Art, Historical Periods, Fantasy/Sci-Fi, Anime, Dark/Atmospheric
