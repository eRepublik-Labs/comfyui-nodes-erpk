<!-- ABOUTME: Help documentation for the Claude Structured Output ComfyUI node. -->
<!-- ABOUTME: Gets JSON from Claude that matches a tool definition's schema via structured outputs. -->

# Claude Structured Output

Gets JSON from Claude that matches a tool definition's schema. Uses Anthropic's structured outputs (`output_config.format` with a JSON Schema), so the reply is constrained to the schema.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | String (multiline) | (empty) | Prompt describing what to extract or generate |
| tool | CLAUDE_TOOLS | (required) | Tool definition from a Tool Definition node. Must contain exactly 1 tool; its `input_schema` is the JSON Schema the reply must match |
| client | CLAUDE_API_CLIENT | (none) | Claude API client (optional if API key is configured in Settings) |
| system_prompt | String (multiline) | (empty) | System prompt to guide extraction behavior (optional) |
| temperature | Float | 0.0 | Ignored (optional). Current Claude models return an error for any temperature, so it is never sent; the widget stays so saved workflows load |
| max_tokens | Int | 4096 | Maximum tokens for the response; thinking counts toward it (optional). Min: 256, Max: 128000, Step: 128 |
| seed | Int | -1 | Cache control. A fixed seed reuses the previous result; -1 re-runs every queue |
| effort | Combo | (model default) | How much effort Claude spends: thinking depth, tool calls and answer length (optional). Options: (model default), low, medium, high, xhigh, max. (model default) sends nothing, so the model keeps its own default (high; medium on Opus 5.5). Higher levels cost more tokens and time |

## Output

| Output | Type | Description |
|--------|------|-------------|
| json_output | String | The JSON reply, pretty-printed |
| thinking | String | Claude's summarized thinking for this reply. Empty when the model answered without thinking |

## Notes

- The tool input must contain exactly 1 tool definition; connecting multiple tools raises an error
- The tool's name and description are added to the system prompt so Claude knows what the JSON is for
- Structured outputs require `"additionalProperties": false` on every object in the schema. The node adds it where the schema leaves it out; a schema that sets it to anything else is rejected before any API call
- A reply cut off at `max_tokens` raises an error asking you to raise `max_tokens` instead of returning partial JSON
- Works on every offered model. Earlier versions forced tool use, which Sonnet 5.5, Opus 5.5 and Fable 5.1 reject
- Use cases: data extraction, metadata generation, classification, structured content generation
- Caching follows the seed: a fixed seed reuses the result you already paid for, while -1 (randomize) re-runs on every queue
