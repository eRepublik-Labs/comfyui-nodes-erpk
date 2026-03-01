<!-- ABOUTME: Help documentation for the Claude Text Generation ComfyUI node. -->
<!-- ABOUTME: General-purpose text generation with configurable temperature and streaming. -->

# Claude Text Generation

General-purpose text generation using Claude for completion, creative writing, and content generation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Text prompt for Claude |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| system_prompt | String (multiline) | (empty) | System prompt to guide Claude's behavior (optional) |
| temperature | Float | 0.7 | Creativity level: 0.0 = focused, 1.0 = creative (optional). Min: 0.0, Max: 1.0, Step: 0.05 |
| max_tokens | Int | 1024 | Maximum length of response (optional). Min: 256, Max: 8192, Step: 128 |
| use_streaming | Boolean | False | Enable streaming responses (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Generated text response |

## Notes

- Re-executes on every queue (not cached) since API responses vary
- Streaming collects all chunks and returns the full response when complete
- The client input is optional — if omitted, the node creates its own client using your configured API key
- Prompt cannot be empty
