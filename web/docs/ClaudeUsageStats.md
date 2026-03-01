<!-- ABOUTME: Help documentation for the Claude Usage Stats ComfyUI node. -->
<!-- ABOUTME: Displays token usage and cost statistics for a Claude client. -->

# Claude Usage Stats

Displays cumulative token usage and cost statistics for a Claude API client session.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| client | CLAUDE_API_CLIENT | (required) | Claude API client to read stats from |
| reset_stats | Boolean | False | Reset usage statistics after displaying (optional) |

## Output

| Output | Type | Description |
|--------|------|-------------|
| stats | String | Formatted usage statistics including token counts and costs |

## Notes

- Shows input tokens, output tokens, cache read tokens, and cache creation tokens
- Displays cost breakdown in USD with cache savings
- This is an output node — it prints stats to the ComfyUI console as well
- Connect at the end of your workflow to monitor cumulative API costs
