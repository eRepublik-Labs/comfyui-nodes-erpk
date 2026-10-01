<!-- ABOUTME: Help documentation for the Claude Token Counter ComfyUI node. -->
<!-- ABOUTME: Counts tokens in text and estimates Claude API costs. -->

# Claude Token Counter

Counts tokens in text and provides cost estimates for Claude API usage. Supports accurate API-based counting or local estimation.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| text | String (multiline) | (empty) | Text to count tokens for |
| model | Combo | claude-sonnet-5-5 | Model for token counting and cost estimation. Options: claude-sonnet-5-5, claude-sonnet-5, claude-opus-5-5, claude-opus-5, claude-fable-5-1, claude-fable-5 |
| client | CLAUDE_API_CLIENT | (none) | Connect a client for accurate API-based counting (optional). Otherwise uses ~4 chars/token estimation |

## Output

| Output | Type | Description |
|--------|------|-------------|
| token_count | Int | Number of tokens in the text |
| summary | String | Formatted analysis with character count, token count, context usage, and cost estimates |

## Notes

- With a client connected: uses the Anthropic token counting API for accurate counts (counted against the client's model)
- Without a client: estimates at ~4 characters per token
- Shows cost estimates for the text as both input and output tokens
- Warns when context usage exceeds 75% or 90% of the model's context window (1M tokens on every offered model)
- Pricing data is loaded from pricing.json and reflects current Anthropic rates
- This is an output node — it prints the summary to the ComfyUI console as well
