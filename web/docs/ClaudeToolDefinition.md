<!-- ABOUTME: Help documentation for the Claude Tool Definition ComfyUI node. -->
<!-- ABOUTME: Builds Anthropic tool definitions visually for use with structured output. -->

# Claude Tool Definition

Builds an Anthropic tool definition visually and chains multiple definitions together. Connect the output to the Structured Output node.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| tool_name | String | (empty) | snake_case tool identifier (e.g., extract_person) |
| description | String (multiline) | (empty) | What this tool does — shown to the model |
| parameters_json | String (multiline) | `{"type": "object", "properties": {}, "required": []}` | JSON Schema for the tool's input parameters |
| previous_tools | CLAUDE_TOOLS | (none) | Chain from another Tool Definition node (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| tools | CLAUDE_TOOLS | Tool definition list, passable to Structured Output or another Tool Definition |

## Notes

- Chain multiple Tool Definition nodes by connecting tools output to the next node's previous_tools input
- If a chained tool has the same name as a previous one, it replaces the earlier definition
- Invalid JSON in parameters_json raises an error at queue time
- The parameters_json must be a JSON object with a "type" field (standard JSON Schema)
- For Structured Output, connect exactly 1 tool definition
