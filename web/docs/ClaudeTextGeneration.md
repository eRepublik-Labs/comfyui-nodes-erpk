<!-- ABOUTME: Help documentation for the Claude Text Generation ComfyUI node. -->
<!-- ABOUTME: General-purpose text generation with configurable effort, max tokens and streaming. -->

# Claude Text Generation

General-purpose text generation using Claude for completion, creative writing, and content generation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Text prompt for Claude |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| system_prompt | String (multiline) | (empty) | System prompt to guide Claude's behavior (optional) |
| temperature | Float | 0.7 | Ignored (optional). Current Claude models return an error for any temperature, so it is never sent; the widget stays so saved workflows load |
| max_tokens | Int | 1024 | Maximum length of response; thinking counts toward it (optional). Min: 256, Max: 128000, Step: 128 |
| use_streaming | Boolean | False | Enable streaming responses (optional) |
| model | Combo | (inherit from client) | Model override for this call (optional). Choose a model from the list, or inherit the connected client's model. Without a client, inherit means the Claude API client's default model |
| effort | Combo | (model default) | How much effort Claude spends: thinking depth, tool calls and answer length (optional). Options: (model default), low, medium, high, xhigh, max. (model default) sends nothing, so the model keeps its own default (high; medium on Opus 5.5). Higher levels cost more tokens and time |

## Output

| Output | Type | Description |
|--------|------|-------------|
| response | String | Generated text response |

## Notes

- Re-executes on every queue (not cached) since API responses vary
- Streaming collects all chunks and returns the full response when complete
- The client input is optional — if omitted, the node creates its own client using your configured API key
- Prompt cannot be empty
