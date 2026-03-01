<!-- ABOUTME: Help documentation for the Claude Structured Output ComfyUI node. -->
<!-- ABOUTME: Forces Claude to respond with guaranteed structured JSON via tool use. -->

# Claude Structured Output

Forces Claude to respond with structured JSON matching a tool schema. Uses Anthropic's forced tool use to guarantee valid JSON output.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Prompt describing what to extract or generate |
| tool | CLAUDE_TOOLS | (required) | Tool definition from a Tool Definition node. Must contain exactly 1 tool |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| system_prompt | String (multiline) | (empty) | System prompt to guide extraction behavior (optional) |
| temperature | Float | 0.0 | Creativity level (optional). Low values recommended for consistent output. Min: 0.0, Max: 1.0, Step: 0.05 |
| max_tokens | Int | 4096 | Maximum tokens for the response (optional). Min: 256, Max: 8192, Step: 128 |

## Output

| Output | Type | Description |
|--------|------|-------------|
| json_output | String | Extracted JSON string (pretty-printed) |
| thinking | String | Any reasoning text Claude produced before the tool use block (usually empty at low temperature) |

## Notes

- The tool input must contain exactly 1 tool definition — connecting multiple tools will raise an error
- Default temperature is 0.0 for maximum consistency
- Use cases: data extraction, metadata generation, classification, structured content generation
- The thinking output captures optional text blocks, not Anthropic's extended thinking feature
- Re-executes on every queue (not cached)
